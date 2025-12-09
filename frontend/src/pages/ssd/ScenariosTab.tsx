import React, { useState } from 'react';
import { Plus, Edit2, Trash2, Play, Loader2, AlertTriangle, CheckCircle, ChevronDown, Zap, Gauge } from 'lucide-react';
import {
    useSSDScenarios, useCreateScenario, useUpdateScenario, useDeleteScenario,
    useSSDCSOAssets, useSSDAnalysisConfigs,
} from '../../api/hooks';
import type { AnalysisScenarioData } from '../../api/hooks';

interface ScenariosTabProps {
    projectId: number;
}

interface EditingScenario {
    id?: number;
    scenario_name: string;
    cso_asset_id: number | null;
    config_id: number | null;
    pff_increase: number;
    pumping_mode: string;
    pump_rate: number;
    time_delay: number;
    flow_return_threshold: number;
    depth_return_threshold: number;
    tank_volume: number | null;
}

const getDefaultScenario = (): EditingScenario => ({
    scenario_name: '',
    cso_asset_id: null,
    config_id: null,
    pff_increase: 0.0,
    pumping_mode: 'Fixed',
    pump_rate: 0.0,
    time_delay: 0,
    flow_return_threshold: 0.0,
    depth_return_threshold: 0.0,
    tank_volume: null,
});

const ScenariosTab: React.FC<ScenariosTabProps> = ({ projectId }) => {
    const { data: scenarios, isLoading: scenariosLoading } = useSSDScenarios(projectId);
    const { data: csoAssets, isLoading: assetsLoading } = useSSDCSOAssets(projectId);
    const { data: configs, isLoading: configsLoading } = useSSDAnalysisConfigs(projectId);
    const createMutation = useCreateScenario();
    const updateMutation = useUpdateScenario();
    const deleteMutation = useDeleteScenario();

    const [editingScenario, setEditingScenario] = useState<EditingScenario | null>(null);
    const [showAdvanced, setShowAdvanced] = useState(false);

    const hasAssets = (csoAssets?.length || 0) > 0;
    const hasConfigs = (configs?.length || 0) > 0;
    const canCreateScenarios = hasAssets && hasConfigs;

    // Helper to get CSO asset name by ID
    const getCSOName = (id: number): string => {
        return csoAssets?.find(a => a.id === id)?.name || `CSO #${id}`;
    };

    // Helper to get config name by ID
    const getConfigName = (id: number): string => {
        return configs?.find(c => c.id === id)?.name || `Config #${id}`;
    };

    const startNewScenario = () => {
        const firstAsset = csoAssets?.[0];
        const firstConfig = configs?.[0];
        setEditingScenario({
            ...getDefaultScenario(),
            scenario_name: `Scenario_${(scenarios?.length || 0) + 1}`,
            cso_asset_id: firstAsset?.id || null,
            config_id: firstConfig?.id || null,
        });
        setShowAdvanced(false);
    };

    const startEditScenario = (scenario: AnalysisScenarioData) => {
        setEditingScenario({
            id: scenario.id,
            scenario_name: scenario.scenario_name,
            cso_asset_id: scenario.cso_asset_id,
            config_id: scenario.config_id,
            pff_increase: scenario.pff_increase,
            pumping_mode: scenario.pumping_mode,
            pump_rate: scenario.pump_rate,
            time_delay: scenario.time_delay,
            flow_return_threshold: scenario.flow_return_threshold,
            depth_return_threshold: scenario.depth_return_threshold,
            tank_volume: scenario.tank_volume,
        });
        setShowAdvanced(scenario.pump_rate > 0 || scenario.tank_volume !== null);
    };

    const cancelEdit = () => {
        setEditingScenario(null);
    };

    const saveScenario = async () => {
        if (!editingScenario) return;

        if (!editingScenario.scenario_name.trim()) {
            alert('Scenario name is required');
            return;
        }
        if (!editingScenario.cso_asset_id) {
            alert('Please select a CSO asset');
            return;
        }
        if (!editingScenario.config_id) {
            alert('Please select a configuration');
            return;
        }

        try {
            const scenarioData = {
                scenario_name: editingScenario.scenario_name,
                cso_asset_id: editingScenario.cso_asset_id,
                config_id: editingScenario.config_id,
                pff_increase: editingScenario.pff_increase,
                pumping_mode: editingScenario.pumping_mode,
                pump_rate: editingScenario.pump_rate,
                time_delay: editingScenario.time_delay,
                flow_return_threshold: editingScenario.flow_return_threshold,
                depth_return_threshold: editingScenario.depth_return_threshold,
                tank_volume: editingScenario.tank_volume,
            };

            if (editingScenario.id) {
                await updateMutation.mutateAsync({
                    projectId,
                    scenarioId: editingScenario.id,
                    update: scenarioData,
                });
            } else {
                await createMutation.mutateAsync({
                    projectId,
                    scenario: scenarioData,
                });
            }
            setEditingScenario(null);
        } catch (error) {
            console.error('Failed to save scenario:', error);
        }
    };

    const deleteScenario = async (scenario: AnalysisScenarioData) => {
        if (!confirm(`Delete scenario "${scenario.scenario_name}"?`)) return;
        try {
            await deleteMutation.mutateAsync({ projectId, scenarioId: scenario.id });
        } catch (error) {
            console.error('Failed to delete scenario:', error);
        }
    };

    if (scenariosLoading || assetsLoading || configsLoading) {
        return (
            <div className="flex justify-center items-center h-32">
                <Loader2 className="animate-spin text-orange-500" size={24} />
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {/* Warning banners */}
            {!hasAssets && (
                <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 flex items-start gap-3">
                    <AlertTriangle className="text-amber-500 flex-shrink-0 mt-0.5" size={20} />
                    <div>
                        <p className="text-amber-800 font-medium">No CSO assets defined</p>
                        <p className="text-amber-600 text-sm">
                            Create CSO assets in the CSO Assets tab first.
                        </p>
                    </div>
                </div>
            )}

            {!hasConfigs && (
                <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 flex items-start gap-3">
                    <AlertTriangle className="text-amber-500 flex-shrink-0 mt-0.5" size={20} />
                    <div>
                        <p className="text-amber-800 font-medium">No analysis configurations defined</p>
                        <p className="text-amber-600 text-sm">
                            Create configurations in the Analysis Configurations tab first.
                        </p>
                    </div>
                </div>
            )}

            {/* Add button */}
            <div className="flex justify-between items-center">
                <p className="text-sm text-gray-500">
                    {scenarios?.length || 0} scenario{scenarios?.length !== 1 ? 's' : ''} defined
                </p>
                <button
                    onClick={startNewScenario}
                    disabled={!canCreateScenarios || !!editingScenario}
                    className="bg-orange-600 text-white px-4 py-2 rounded-lg hover:bg-orange-700 transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 font-medium"
                >
                    <Plus size={18} />
                    Add Scenario
                </button>
            </div>

            {/* New/Edit form card */}
            {editingScenario && (
                <div className="bg-orange-50 border-2 border-orange-300 rounded-xl p-5">
                    <h3 className="text-lg font-semibold text-orange-800 mb-4">
                        {editingScenario.id ? 'Edit Scenario' : 'New Scenario'}
                    </h3>
                    <div className="space-y-4">
                        {/* Scenario Name */}
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Scenario Name *</label>
                            <input
                                type="text"
                                value={editingScenario.scenario_name}
                                onChange={(e) => setEditingScenario({ ...editingScenario, scenario_name: e.target.value })}
                                className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-orange-500 focus:border-orange-500"
                                placeholder="e.g. Beech Ave 10SPA"
                            />
                        </div>

                        {/* CSO Asset and Configuration */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">CSO Asset *</label>
                                <select
                                    value={editingScenario.cso_asset_id || ''}
                                    onChange={(e) => setEditingScenario({ ...editingScenario, cso_asset_id: parseInt(e.target.value) || null })}
                                    className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-orange-500 focus:border-orange-500"
                                >
                                    <option value="">Select CSO asset...</option>
                                    {csoAssets?.map((asset) => (
                                        <option key={asset.id} value={asset.id}>{asset.name}</option>
                                    ))}
                                </select>
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Configuration *</label>
                                <select
                                    value={editingScenario.config_id || ''}
                                    onChange={(e) => setEditingScenario({ ...editingScenario, config_id: parseInt(e.target.value) || null })}
                                    className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-orange-500 focus:border-orange-500"
                                >
                                    <option value="">Select configuration...</option>
                                    {configs?.map((config) => (
                                        <option key={config.id} value={config.id}>{config.name}</option>
                                    ))}
                                </select>
                            </div>
                        </div>

                        {/* PFF Increase */}
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">PFF Increase (m³/s)</label>
                            <input
                                type="number"
                                step="0.01"
                                value={editingScenario.pff_increase}
                                onChange={(e) => setEditingScenario({ ...editingScenario, pff_increase: parseFloat(e.target.value) || 0 })}
                                className="w-40 border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-orange-500 focus:border-orange-500"
                            />
                            <span className="text-xs text-gray-500 ml-2">Pass Forward Flow increase</span>
                        </div>

                        {/* Advanced Settings Toggle */}
                        <button
                            type="button"
                            onClick={() => setShowAdvanced(!showAdvanced)}
                            className="flex items-center gap-2 text-sm text-gray-600 hover:text-gray-800"
                        >
                            <ChevronDown className={`transform transition ${showAdvanced ? 'rotate-180' : ''}`} size={16} />
                            Pumping & Tank Settings
                        </button>

                        {showAdvanced && (
                            <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 space-y-4">
                                {/* Pumping */}
                                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-1">Pumping Mode</label>
                                        <select
                                            value={editingScenario.pumping_mode}
                                            onChange={(e) => setEditingScenario({ ...editingScenario, pumping_mode: e.target.value })}
                                            className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-orange-500 focus:border-orange-500"
                                        >
                                            <option value="Fixed">Fixed</option>
                                            <option value="Variable">Variable</option>
                                        </select>
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-1">Pump Rate (m³/s)</label>
                                        <input
                                            type="number"
                                            step="0.01"
                                            value={editingScenario.pump_rate}
                                            onChange={(e) => setEditingScenario({ ...editingScenario, pump_rate: parseFloat(e.target.value) || 0 })}
                                            className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-orange-500 focus:border-orange-500"
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-1">Time Delay (hours)</label>
                                        <input
                                            type="number"
                                            value={editingScenario.time_delay}
                                            onChange={(e) => setEditingScenario({ ...editingScenario, time_delay: parseInt(e.target.value) || 0 })}
                                            className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-orange-500 focus:border-orange-500"
                                        />
                                    </div>
                                </div>

                                {/* Flow Return Thresholds */}
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-1">Flow Return Threshold (m³/s)</label>
                                        <input
                                            type="number"
                                            step="0.01"
                                            value={editingScenario.flow_return_threshold}
                                            onChange={(e) => setEditingScenario({ ...editingScenario, flow_return_threshold: parseFloat(e.target.value) || 0 })}
                                            className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-orange-500 focus:border-orange-500"
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-1">Depth Return Threshold (m)</label>
                                        <input
                                            type="number"
                                            step="0.1"
                                            value={editingScenario.depth_return_threshold}
                                            onChange={(e) => setEditingScenario({ ...editingScenario, depth_return_threshold: parseFloat(e.target.value) || 0 })}
                                            className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-orange-500 focus:border-orange-500"
                                        />
                                    </div>
                                </div>

                                {/* Tank Volume */}
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">Tank Volume (m³)</label>
                                    <input
                                        type="number"
                                        step="10"
                                        value={editingScenario.tank_volume ?? ''}
                                        onChange={(e) => setEditingScenario({ ...editingScenario, tank_volume: e.target.value ? parseFloat(e.target.value) : null })}
                                        placeholder="For Model 2 (Fixed Tank)"
                                        className="w-48 border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-orange-500 focus:border-orange-500"
                                    />
                                </div>
                            </div>
                        )}

                        <div className="flex gap-3 pt-2">
                            <button
                                onClick={saveScenario}
                                disabled={createMutation.isPending || updateMutation.isPending}
                                className="bg-orange-600 text-white px-4 py-2 rounded-lg hover:bg-orange-700 transition disabled:opacity-50 flex items-center gap-2"
                            >
                                {(createMutation.isPending || updateMutation.isPending) ? (
                                    <Loader2 className="animate-spin" size={16} />
                                ) : (
                                    <CheckCircle size={16} />
                                )}
                                {editingScenario.id ? 'Save Changes' : 'Create Scenario'}
                            </button>
                            <button
                                onClick={cancelEdit}
                                className="bg-gray-200 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-300 transition"
                            >
                                Cancel
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Scenario cards */}
            <div className="space-y-3">
                {scenarios?.map((scenario) => (
                    <div
                        key={scenario.id}
                        className="bg-white border border-gray-200 rounded-xl p-5 hover:border-orange-300 transition"
                    >
                        <div className="flex items-start justify-between">
                            <div className="flex items-center gap-3">
                                <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
                                    <Play className="text-purple-600" size={20} />
                                </div>
                                <div>
                                    <h4 className="font-semibold text-gray-900">{scenario.scenario_name}</h4>
                                    <p className="text-xs text-gray-400">
                                        {getCSOName(scenario.cso_asset_id)} • {getConfigName(scenario.config_id)}
                                    </p>
                                </div>
                            </div>
                            <div className="flex gap-2">
                                <button
                                    onClick={() => startEditScenario(scenario)}
                                    disabled={!!editingScenario}
                                    className="p-2 text-gray-400 hover:text-orange-600 hover:bg-orange-50 rounded-lg transition disabled:opacity-50"
                                    title="Edit"
                                >
                                    <Edit2 size={16} />
                                </button>
                                <button
                                    onClick={() => deleteScenario(scenario)}
                                    disabled={deleteMutation.isPending}
                                    className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition disabled:opacity-50"
                                    title="Delete"
                                >
                                    <Trash2 size={16} />
                                </button>
                            </div>
                        </div>

                        <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                            <div>
                                <p className="text-gray-500 mb-1 flex items-center gap-1">
                                    <Zap size={14} /> PFF Increase
                                </p>
                                <span className="font-medium text-gray-900">{scenario.pff_increase} m³/s</span>
                            </div>
                            <div>
                                <p className="text-gray-500 mb-1 flex items-center gap-1">
                                    <Gauge size={14} /> Pump Rate
                                </p>
                                <span className="font-medium text-gray-900">
                                    {scenario.pump_rate > 0 ? `${scenario.pump_rate} m³/s` : 'None'}
                                </span>
                            </div>
                            {scenario.tank_volume !== null && (
                                <div>
                                    <p className="text-gray-500 mb-1">Tank Volume</p>
                                    <span className="font-medium text-cyan-700">{scenario.tank_volume} m³</span>
                                </div>
                            )}
                            <div>
                                <p className="text-gray-500 mb-1">Pumping Mode</p>
                                <span className="font-medium text-gray-900">{scenario.pumping_mode}</span>
                            </div>
                        </div>
                    </div>
                ))}
            </div>

            {(!scenarios || scenarios.length === 0) && !editingScenario && (
                <div className="text-center py-12 text-gray-400">
                    <Play size={48} className="mx-auto mb-4 opacity-50" />
                    <p>No analysis scenarios defined yet</p>
                    <p className="text-sm mt-2">
                        {canCreateScenarios
                            ? 'Click "Add Scenario" to create one.'
                            : 'Define CSO assets and configurations first.'}
                    </p>
                </div>
            )}
        </div>
    );
};

export default ScenariosTab;
