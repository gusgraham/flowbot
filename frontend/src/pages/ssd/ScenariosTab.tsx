import React, { useState } from 'react';
import { Plus, Edit2, Trash2, Play, Loader2, AlertTriangle, CheckCircle, ChevronDown, Zap, Gauge, X } from 'lucide-react';
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

interface DevelopFormData {
    baseName: string;
    csoAssetId: number | null;
    configId: number | null;
    pffIncrease: number;
    pffAtFs: number;
    dwf: number;
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

const defaultDevelopData: DevelopFormData = {
    baseName: '',
    csoAssetId: null,
    configId: null,
    pffIncrease: 0,
    pffAtFs: 0,
    dwf: 0
};

const ScenariosTab: React.FC<ScenariosTabProps> = ({ projectId }) => {
    const { data: scenarios, isLoading: scenariosLoading } = useSSDScenarios(projectId);
    const { data: csoAssets, isLoading: assetsLoading } = useSSDCSOAssets(projectId);
    const { data: configs, isLoading: configsLoading } = useSSDAnalysisConfigs(projectId);
    const createMutation = useCreateScenario();
    const updateMutation = useUpdateScenario();
    const deleteMutation = useDeleteScenario();

    const [editingScenario, setEditingScenario] = useState<EditingScenario | null>(null);
    const [showAdvanced, setShowAdvanced] = useState(false);

    // Develop Scenarios State
    const [developModalOpen, setDevelopModalOpen] = useState(false);
    const [developData, setDevelopData] = useState<DevelopFormData>(defaultDevelopData);
    const [isDeveloping, setIsDeveloping] = useState(false);

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

    const openDevelopModal = () => {
        const firstAsset = csoAssets?.[0];
        const firstConfig = configs?.[0];
        setDevelopData({
            ...defaultDevelopData,
            csoAssetId: firstAsset?.id || null,
            configId: firstConfig?.id || null
        });
        setDevelopModalOpen(true);
    };

    const handleDevelopSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        const { baseName, csoAssetId, configId, pffIncrease, pffAtFs, dwf } = developData;

        if (!baseName.trim() || !csoAssetId || !configId) {
            alert('Please fill in all required fields');
            return;
        }

        setIsDeveloping(true);

        try {
            const calcScenario = (suffix: string, frt: number) => {
                const pumpRate = (0.95 * pffAtFs) - frt;
                // Ensure pumpRate is not negative
                const safePumpRate = Math.max(0, pumpRate);

                return {
                    scenario_name: `${baseName}${suffix}`,
                    cso_asset_id: csoAssetId,
                    config_id: configId,
                    pff_increase: pffIncrease,
                    pumping_mode: 'Fixed',
                    pump_rate: safePumpRate,
                    time_delay: 0,
                    flow_return_threshold: frt,
                    depth_return_threshold: 10,
                    tank_volume: null // Optimise tank volume
                };
            };

            const scenariosToCreate = [
                calcScenario('_Avg', (pffAtFs + 3 * dwf) / 2),
                calcScenario('_3DWF', 3 * dwf),
                calcScenario('_2DWF', 2 * dwf),
                calcScenario('_DWF', dwf)
            ];

            await Promise.all(scenariosToCreate.map(scenario =>
                createMutation.mutateAsync({ projectId, scenario })
            ));

            setDevelopModalOpen(false);
            setDevelopData(defaultDevelopData);
        } catch (error) {
            console.error("Failed to develop scenarios:", error);
            alert("Failed to create scenarios. Please check the logs.");
        } finally {
            setIsDeveloping(false);
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

            {/* Action Bar */}
            <div className="flex justify-between items-center">
                <p className="text-sm text-gray-500">
                    {scenarios?.length || 0} scenario{scenarios?.length !== 1 ? 's' : ''} defined
                </p>
                <div className="flex gap-2">
                    <button
                        onClick={openDevelopModal}
                        disabled={!canCreateScenarios || !!editingScenario}
                        className="bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700 transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 font-medium shadow-sm"
                        title="Auto-create 4 standard scenarios"
                    >
                        <Zap size={18} />
                        Develop Scenarios
                    </button>
                    <button
                        onClick={startNewScenario}
                        disabled={!canCreateScenarios || !!editingScenario}
                        className="bg-orange-600 text-white px-4 py-2 rounded-lg hover:bg-orange-700 transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 font-medium shadow-sm"
                    >
                        <Plus size={18} />
                        Add Scenario
                    </button>
                </div>
            </div>

            {/* New/Edit form card */}
            {editingScenario && (
                <div className="bg-orange-50 border-2 border-orange-300 rounded-xl p-5">
                    <h3 className="text-lg font-semibold text-orange-800 mb-4">
                        {editingScenario.id ? 'Edit Scenario' : 'New Scenario'}
                    </h3>
                    {/* Existing Scenario Form Fields */}
                    <div className="space-y-4">
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

                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">PFF Increase (m³/s)</label>
                            <input
                                type="number"
                                step="0.01"
                                value={editingScenario.pff_increase}
                                onChange={(e) => setEditingScenario({ ...editingScenario, pff_increase: parseFloat(e.target.value) || 0 })}
                                className="w-40 border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-orange-500 focus:border-orange-500"
                            />
                        </div>

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
                                    {scenario.pump_rate > 0 ? `${scenario.pump_rate.toFixed(3)} m³/s` : 'None'}
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

            {/* Develop Scenarios Modal */}
            {developModalOpen && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
                    <div className="bg-white rounded-xl max-w-2xl w-full p-6 shadow-xl">
                        <div className="flex justify-between items-center mb-6">
                            <div className="flex items-center gap-2">
                                <div className="p-2 bg-indigo-100 rounded-lg">
                                    <Zap className="text-indigo-600" size={24} />
                                </div>
                                <div>
                                    <h2 className="text-xl font-bold text-gray-900">Develop Scenarios</h2>
                                    <p className="text-sm text-gray-500">Auto-generate 4 standard scenarios based on flow parameters</p>
                                </div>
                            </div>
                            <button
                                onClick={() => setDevelopModalOpen(false)}
                                className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                            >
                                <X size={20} className="text-gray-500" />
                            </button>
                        </div>

                        <form onSubmit={handleDevelopSubmit} className="space-y-6">
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                                {/* Left Column: Basic Setup */}
                                <div className="space-y-4">
                                    <h3 className="text-sm font-semibold text-gray-900 border-b pb-2">Configuration</h3>
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-1">Base Name *</label>
                                        <input
                                            className="w-full border border-gray-300 rounded-lg p-2.5 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition"
                                            placeholder="e.g. Beech Ave"
                                            value={developData.baseName}
                                            onChange={(e) => setDevelopData({ ...developData, baseName: e.target.value })}
                                            required
                                        />
                                        <p className="text-xs text-gray-500 mt-1">Suffixes (_Avg, _3DWF, etc.) will be added</p>
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-1">CSO Asset *</label>
                                        <select
                                            value={developData.csoAssetId || ''}
                                            onChange={(e) => setDevelopData({ ...developData, csoAssetId: parseInt(e.target.value) || null })}
                                            className="w-full border border-gray-300 rounded-lg p-2.5 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition"
                                            required
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
                                            value={developData.configId || ''}
                                            onChange={(e) => setDevelopData({ ...developData, configId: parseInt(e.target.value) || null })}
                                            className="w-full border border-gray-300 rounded-lg p-2.5 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition"
                                            required
                                        >
                                            <option value="">Select configuration...</option>
                                            {configs?.map((config) => (
                                                <option key={config.id} value={config.id}>{config.name}</option>
                                            ))}
                                        </select>
                                    </div>
                                </div>

                                {/* Right Column: Flow Parameters */}
                                <div className="space-y-4">
                                    <h3 className="text-sm font-semibold text-gray-900 border-b pb-2">Flow Parameters</h3>
                                    <div>
                                        <label className="block text-sm font-medium text-gray-700 mb-1">PFF Increase (m³/s)</label>
                                        <input
                                            type="number"
                                            step="0.001"
                                            className="w-full border border-gray-300 rounded-lg p-2.5 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition"
                                            value={developData.pffIncrease}
                                            onChange={(e) => setDevelopData({ ...developData, pffIncrease: parseFloat(e.target.value) || 0 })}
                                        />
                                    </div>
                                    <div className="bg-indigo-50 p-4 rounded-xl space-y-4 border border-indigo-100">
                                        <div>
                                            <label className="block text-sm font-bold text-indigo-900 mb-1">PFF @ First Spill (m³/s)</label>
                                            <input
                                                type="number"
                                                step="0.001"
                                                className="w-full border border-indigo-200 rounded-lg p-2.5 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition bg-white"
                                                value={developData.pffAtFs}
                                                onChange={(e) => setDevelopData({ ...developData, pffAtFs: parseFloat(e.target.value) || 0 })}
                                                required
                                            />
                                        </div>
                                        <div>
                                            <label className="block text-sm font-bold text-indigo-900 mb-1">Dry Weather Flow (DWF) (m³/s)</label>
                                            <input
                                                type="number"
                                                step="0.001"
                                                className="w-full border border-indigo-200 rounded-lg p-2.5 focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition bg-white"
                                                value={developData.dwf}
                                                onChange={(e) => setDevelopData({ ...developData, dwf: parseFloat(e.target.value) || 0 })}
                                                required
                                            />
                                        </div>
                                    </div>
                                </div>
                            </div>

                            <div className="flex justify-end gap-3 pt-4 border-t border-gray-100">
                                <button
                                    type="button"
                                    onClick={() => setDevelopModalOpen(false)}
                                    className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
                                >
                                    Cancel
                                </button>
                                <button
                                    type="submit"
                                    disabled={isDeveloping}
                                    className="px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors disabled:opacity-50 flex items-center shadow-md font-medium"
                                >
                                    {isDeveloping && <Loader2 className="animate-spin mr-2" size={16} />}
                                    Generate 4 Scenarios
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
};

export default ScenariosTab;
