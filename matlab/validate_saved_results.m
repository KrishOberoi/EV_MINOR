function validate_saved_results()
%VALIDATE_SAVED_RESULTS Independently check committed Python CSV artifacts.
%
% This script intentionally reads saved outputs rather than calling the
% Python simulation functions. It checks conservation and metric invariants
% from a second numerical environment.

scriptDir = fileparts(mfilename('fullpath'));
rootDir = fileparts(scriptDir);
csvDir = fullfile(rootDir, 'results', 'csv');

trajectories = readtable(fullfile(csvDir, 'four_cell_pack_trajectories.csv'));
pack = readtable(fullfile(csvDir, 'four_cell_pack_summary.csv'));
cells = readtable(fullfile(csvDir, 'four_cell_pack_cell_summary.csv'));
balancing = readtable(fullfile(csvDir, 'balancing_comparison_timeseries.csv'));
metrics = readtable(fullfile(csvDir, 'balancing_comparison_metrics.csv'));

tol = 1e-8;
check_table_finite(trajectories, 'pack trajectories');
check_table_finite(pack, 'pack summary');
check_table_finite(cells, 'cell summary');
check_table_finite(balancing, 'balancing trajectories');
check_table_finite(metrics, 'balancing metrics');

% Series-connected cells carry the same externally applied current, and pack
% voltage is the sum of the individual cell voltages.
packTimes = unique(trajectories.time_s);
for k = 1:numel(packTimes)
    t = packTimes(k);
    rows = abs(trajectories.time_s - t) < tol;
    currents = trajectories.current_A(rows);
    assert(max(currents) - min(currents) < tol, ...
        'Common series current invariant failed at t=%g.', t);

    packRow = abs(pack.time_s - t) < tol;
    assert(nnz(packRow) == 1, 'Pack summary has an unexpected time at t=%g.', t);
    reconstructedVoltage = sum(trajectories.voltage_V(rows));
    assert(abs(reconstructedVoltage - pack.pack_voltage_V(packRow)) < tol, ...
        'Pack voltage summation failed at t=%g.', t);
end

cellNames = string(cells.cell);
capacity = zeros(size(cellNames));
for k = 1:numel(cellNames)
    capacity(k) = cells.capacity_ah(k);
end

controllers = unique(string(balancing.controller), 'stable');
for c = 1:numel(controllers)
    controller = controllers(c);
    rowsController = string(balancing.controller) == controller;
    data = balancing(rowsController, :);
    times = unique(data.time_s);

    % Ideal balancing is lossless in this control-oriented layer.
    for k = 1:numel(times)
        t = times(k);
        rows = abs(data.time_s - t) < tol;
        assert(abs(sum(data.balancing_current_A(rows))) < tol, ...
            'Non-conservative transfer in %s at t=%g.', controller, t);
    end

    decompositionError = data.cell_current_A - data.pack_current_A - data.balancing_current_A;
    assert(max(abs(decompositionError)) < tol, ...
        'Current decomposition failed for %s.', controller);

    % Reconstruct SOC using the actual stored time interval, not a nominal
    % timestep. This catches duplicated or missing boundary rows.
    dataCells = unique(string(data.cell), 'stable');
    for j = 1:numel(dataCells)
        cellName = dataCells(j);
        rowsCell = string(data.cell) == cellName;
        series = data(rowsCell, :);
        [~, order] = sort(series.time_s);
        series = series(order, :);
        cellCapacity = capacity(cellNames == cellName);
        reconstructedSoc = zeros(height(series), 1);
        reconstructedSoc(1) = series.soc(1);
        for k = 1:(height(series) - 1)
            dt = series.time_s(k + 1) - series.time_s(k);
            reconstructedSoc(k + 1) = reconstructedSoc(k) ...
                - series.cell_current_A(k) * dt / (3600 * cellCapacity);
        end
        assert(max(abs(reconstructedSoc - series.soc)) < tol, ...
            'SOC propagation failed for %s / %s.', controller, cellName);
    end

    finalTime = max(data.time_s);
    finalRows = abs(data.time_s - finalTime) < tol;
    finalVoltageSpread = max(data.voltage_V(finalRows)) - min(data.voltage_V(finalRows));
    finalSocSpread = max(data.soc(finalRows)) - min(data.soc(finalRows));
    metricRow = string(metrics.controller) == controller;
    assert(nnz(metricRow) == 1, 'Missing metric row for %s.', controller);
    assert(abs(finalVoltageSpread * 1000 - metrics.final_voltage_spread_mV(metricRow)) < tol, ...
        'Final voltage metric mismatch for %s.', controller);
    assert(abs(finalSocSpread * 100 - metrics.final_soc_spread_percentage_points(metricRow)) < tol, ...
        'Final SOC metric mismatch for %s.', controller);
    assert(metrics.balancing_energy_Wh(metricRow) >= -tol, ...
        'Negative balancing energy for %s.', controller);
end

initialRows = abs(balancing.time_s - min(balancing.time_s)) < tol;
initialSpreads = zeros(numel(controllers), 1);
for c = 1:numel(controllers)
    rows = initialRows & string(balancing.controller) == controllers(c);
    initialSpreads(c) = max(balancing.soc(rows)) - min(balancing.soc(rows));
end
assert(max(initialSpreads) - min(initialSpreads) < tol, ...
    'Controllers do not share the same initial SOC spread.');

fprintf('MATLAB validation passed.\n');
fprintf('Checked %d pack rows and %d controller rows.\n', height(trajectories), height(balancing));
fprintf(['Verified common series current, pack-voltage summation, zero-net ', ...
    'transfer, current decomposition, SOC propagation, and metric reconstruction.\n']);
end

function check_table_finite(data, label)
% Check all numeric columns and all text columns for missing values.
variables = data.Properties.VariableNames;
for k = 1:numel(variables)
    column = data.(variables{k});
    if isnumeric(column)
        assert(all(isfinite(column(:))), 'Non-finite value in %s.', label);
    else
        missing = ismissing(string(column));
        assert(~any(missing(:)), 'Missing value in %s.', label);
    end
end
end
