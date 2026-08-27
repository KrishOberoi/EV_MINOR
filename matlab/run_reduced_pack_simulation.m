function run_reduced_pack_simulation()
%RUN_REDUCED_PACK_SIMULATION Run a transparent MATLAB 4-cell 1-RC sanity model.
%
% This is deliberately a control-oriented model. It is not the project's
% electrochemical reference model, which remains the Python/PyBaMM SPM.

scriptDir = fileparts(mfilename('fullpath'));
rootDir = fileparts(scriptDir);
csvDir = fullfile(rootDir, 'results', 'csv');
plotDir = fullfile(rootDir, 'results', 'plots');
if ~exist(csvDir, 'dir')
    mkdir(csvDir);
end
if ~exist(plotDir, 'dir')
    mkdir(plotDir);
end

% Match the Python four-cell baseline profile: 20 min at 2.5 A, 10 min
% rest, 20 min at 1.25 A, and 10 min rest.
dt = 10;
time_s = (0:dt:3600)';
current_A = zeros(size(time_s));
current_A(time_s < 1200) = 2.5;
current_A(time_s >= 1800 & time_s < 3000) = 1.25;

% Heterogeneous pack configuration from the Python experiment.
initialSoc = [0.80; 0.76; 0.72; 0.78];
capacityAh = [5.00; 4.90; 4.70; 4.95];
R0 = [0.012; 0.015; 0.022; 0.010];
R1 = [0.006; 0.008; 0.010; 0.005];
tau_s = [120; 120; 120; 120];
numCells = numel(initialSoc);
numSamples = numel(time_s);

soc = zeros(numCells, numSamples);
polarization_V = zeros(numCells, numSamples);
voltage_V = zeros(numCells, numSamples);
soc(:, 1) = initialSoc;

for k = 1:numSamples
    % Discharge current is positive. The model uses the same current in all
    % series cells, while the parameters create cell-to-cell variation.
    voltage_V(:, k) = ocv_from_soc(soc(:, k)) ...
        - current_A(k) .* R0 - polarization_V(:, k);

    if k < numSamples
        soc(:, k + 1) = soc(:, k) ...
            - current_A(k) * dt ./ (3600 .* capacityAh);
        soc(:, k + 1) = min(max(soc(:, k + 1), 0), 1);
        decay = exp(-dt ./ tau_s);
        polarization_V(:, k + 1) = decay .* polarization_V(:, k) ...
            + R1 .* (1 - decay) .* current_A(k);
    end
end

% Long format trajectory file for straightforward MATLAB/Python comparison.
numRows = numCells * numSamples;
cellColumn = cell(numRows, 1);
timeColumn = zeros(numRows, 1);
currentColumn = zeros(numRows, 1);
voltageColumn = zeros(numRows, 1);
socColumn = zeros(numRows, 1);
row = 0;
for i = 1:numCells
    indices = (row + 1):(row + numSamples);
    cellColumn(indices) = repmat({sprintf('Cell %d', i)}, numSamples, 1);
    timeColumn(indices) = time_s;
    currentColumn(indices) = current_A;
    voltageColumn(indices) = voltage_V(i, :)';
    socColumn(indices) = soc(i, :)';
    row = row + numSamples;
end

trajectories = table(cellColumn, timeColumn, currentColumn, voltageColumn, socColumn, ...
    'VariableNames', {'cell', 'time_s', 'current_A', 'voltage_V', 'soc'});
writetable(trajectories, fullfile(csvDir, 'matlab_reduced_pack_trajectories.csv'));

packVoltage = sum(voltage_V, 1)';
packSummary = table(time_s, packVoltage, min(voltage_V, [], 1)', ...
    max(voltage_V, [], 1)', max(voltage_V, [], 1)' - min(voltage_V, [], 1)', ...
    min(soc, [], 1)', max(soc, [], 1)', max(soc, [], 1)' - min(soc, [], 1)', ...
    'VariableNames', {'time_s', 'pack_voltage_V', 'minimum_cell_voltage_V', ...
    'maximum_cell_voltage_V', 'cell_voltage_spread_V', 'minimum_cell_soc', ...
    'maximum_cell_soc', 'cell_soc_spread'});
writetable(packSummary, fullfile(csvDir, 'matlab_reduced_pack_summary.csv'));

fig = figure('Visible', 'off', 'Color', 'w');
subplot(2, 1, 1);
plot(time_s / 60, voltage_V', 'LineWidth', 1.2);
xlabel('Time (min)');
ylabel('Cell voltage (V)');
title('MATLAB reduced-order four-cell pack');
legend('Cell 1', 'Cell 2', 'Cell 3', 'Cell 4', 'Location', 'best');
grid on;
subplot(2, 1, 2);
plot(time_s / 60, 100 * soc', 'LineWidth', 1.2);
xlabel('Time (min)');
ylabel('SOC (%)');
grid on;
saveas(fig, fullfile(plotDir, 'matlab_reduced_pack.png'));
close(fig);

fprintf('MATLAB reduced-order pack simulation completed.\n');
fprintf('Peak voltage spread: %.3f mV.\n', 1000 * max(packSummary.cell_voltage_spread_V));
fprintf('Final SOC spread: %.3f percentage points.\n', 100 * packSummary.cell_soc_spread(end));
end

function voltage = ocv_from_soc(soc)
% Smooth enough lookup for a transparent Thevenin sanity model.
socGrid = [0.00, 0.05, 0.10, 0.20, 0.40, 0.60, 0.80, 1.00];
voltageGrid = [3.00, 3.25, 3.40, 3.55, 3.68, 3.76, 3.90, 4.20];
voltage = interp1(socGrid, voltageGrid, soc, 'pchip', 'extrap');
end
