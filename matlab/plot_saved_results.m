function plot_saved_results()
%PLOT_SAVED_RESULTS Create MATLAB figures from committed CSV artifacts.

scriptDir = fileparts(mfilename('fullpath'));
rootDir = fileparts(scriptDir);
csvDir = fullfile(rootDir, 'results', 'csv');
plotDir = fullfile(rootDir, 'results', 'plots');
if ~exist(plotDir, 'dir')
    mkdir(plotDir);
end

pack = readtable(fullfile(csvDir, 'four_cell_pack_trajectories.csv'));
metrics = readtable(fullfile(csvDir, 'balancing_comparison_metrics.csv'));

% Python/PyBaMM pack baseline, displayed independently from the reduced-order
% MATLAB model so that model sources are not mixed.
fig1 = figure('Visible', 'off', 'Color', 'w');
subplot(2, 1, 1);
hold on;
cells = unique(string(pack.cell), 'stable');
colors = lines(numel(cells));
for k = 1:numel(cells)
    rows = string(pack.cell) == cells(k);
    plot(pack.time_s(rows) / 60, pack.voltage_V(rows), 'LineWidth', 1.2, ...
        'Color', colors(k, :), 'DisplayName', char(cells(k)));
end
xlabel('Time (min)');
ylabel('Cell voltage (V)');
title('Python/PyBaMM four-cell pack baseline');
legend('Location', 'best');
grid on;

subplot(2, 1, 2);
hold on;
for k = 1:numel(cells)
    rows = string(pack.cell) == cells(k);
    plot(pack.time_s(rows) / 60, 100 * pack.soc(rows), 'LineWidth', 1.2, ...
        'Color', colors(k, :), 'DisplayName', char(cells(k)));
end
xlabel('Time (min)');
ylabel('SOC (%)');
grid on;
saveas(fig1, fullfile(plotDir, 'matlab_python_pack_baseline.png'));
close(fig1);

% Controller metrics are plotted from the saved Python comparison output.
controllers = string(metrics.controller);
fig2 = figure('Visible', 'off', 'Color', 'w');
subplot(1, 2, 1);
bar(categorical(controllers), metrics.final_soc_spread_percentage_points);
ylabel('Final SOC spread (percentage points)');
title('Balancing comparison');
grid on;

subplot(1, 2, 2);
bar(categorical(controllers), metrics.balancing_energy_Wh);
ylabel('Balancing energy (Wh)');
title('Balancing effort');
grid on;
saveas(fig2, fullfile(plotDir, 'matlab_controller_metrics.png'));
close(fig2);

fprintf('MATLAB plots written to %s.\n', plotDir);
end
