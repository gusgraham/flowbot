import React, { useState } from 'react';
import { Plus, Edit2, Trash2, Settings, Loader2, Calendar, Target, CheckCircle, ChevronDown, AlertTriangle } from 'lucide-react';
import {
    useSSDAnalysisConfigs, useCreateAnalysisConfig, useUpdateAnalysisConfig, useDeleteAnalysisConfig,
    useSSDDateRange,
} from '../../api/hooks';
import type { AnalysisConfigDB } from '../../api/hooks';

interface AnalysisConfigsTabProps {
    projectId: number;
}

interface EditingConfig {
    id?: number;
    name: string;
    mode: string;
    model: number;
    start_date: string;
    end_date: string;
    spill_target: number;
    spill_target_bathing: number | null;
    bathing_season_start: string;
    bathing_season_end: string;
    spill_flow_threshold: number;
    spill_volume_threshold: number;
}

const MODES = ['Default Mode', 'Catchment Based Mode', 'WWTW Mode'];
const MODELS: { [key: number]: string } = {
    1: 'Spill Target Assessment',
    2: 'Storage Volume Assessment',
    3: 'Yorkshire Water Method',
    4: 'Bathing Season Assessment',
};

const getDefaultConfig = (): EditingConfig => ({
    name: '',
    mode: 'Default Mode',
    model: 1,
    start_date: '',
    end_date: '',
    spill_target: 10,
    spill_target_bathing: null,
    bathing_season_start: '15/05',
    bathing_season_end: '30/09',
    spill_flow_threshold: 0.001,
    spill_volume_threshold: 0.0,
});

const AnalysisConfigsTab: React.FC<AnalysisConfigsTabProps> = ({ projectId }) => {
    const { data: configs, isLoading } = useSSDAnalysisConfigs(projectId);
    const { data: dateRange } = useSSDDateRange(projectId);
    const createMutation = useCreateAnalysisConfig();
    const updateMutation = useUpdateAnalysisConfig();
    const deleteMutation = useDeleteAnalysisConfig();

    const [editingConfig, setEditingConfig] = useState<EditingConfig | null>(null);
    const [showAdvanced, setShowAdvanced] = useState(false);

    // Format date for datetime-local input
    const formatDateForInput = (isoDate: string | null) => {
        if (!isoDate) return '';
        return isoDate.slice(0, 16);
    };

    const minDate = formatDateForInput(dateRange?.min_date ?? null);
    const maxDate = formatDateForInput(dateRange?.max_date ?? null);
    const hasDateRange = !!minDate && !!maxDate;

    const startNewConfig = () => {
        setEditingConfig({
            ...getDefaultConfig(),
            name: `Config_${(configs?.length || 0) + 1}`,
            // Pre-fill with data range if available
            start_date: minDate,
            end_date: maxDate,
        });
        setShowAdvanced(false);
    };

    const startEditConfig = (config: AnalysisConfigDB) => {
        setEditingConfig({
            id: config.id,
            name: config.name,
            mode: config.mode,
            model: config.model,
            start_date: config.start_date.slice(0, 16), // Format for datetime-local
            end_date: config.end_date.slice(0, 16),
            spill_target: config.spill_target,
            spill_target_bathing: config.spill_target_bathing,
            bathing_season_start: config.bathing_season_start || '15/05',
            bathing_season_end: config.bathing_season_end || '30/09',
            spill_flow_threshold: config.spill_flow_threshold,
            spill_volume_threshold: config.spill_volume_threshold,
        });
        setShowAdvanced(config.model === 4);
    };

    const cancelEdit = () => {
        setEditingConfig(null);
    };

    const saveConfig = async () => {
        if (!editingConfig) return;

        if (!editingConfig.name.trim()) {
            alert('Configuration name is required');
            return;
        }
        if (!editingConfig.start_date || !editingConfig.end_date) {
            alert('Start and end dates are required');
            return;
        }
        if (editingConfig.model === 4 && editingConfig.spill_target_bathing === null) {
            alert('Bathing season spill target is required for Model 4');
            return;
        }

        try {
            const configData = {
                name: editingConfig.name,
                mode: editingConfig.mode,
                model: editingConfig.model,
                start_date: editingConfig.start_date,
                end_date: editingConfig.end_date,
                spill_target: editingConfig.spill_target,
                spill_target_bathing: editingConfig.model === 4 ? editingConfig.spill_target_bathing : null,
                bathing_season_start: editingConfig.model === 4 ? editingConfig.bathing_season_start : null,
                bathing_season_end: editingConfig.model === 4 ? editingConfig.bathing_season_end : null,
                spill_flow_threshold: editingConfig.spill_flow_threshold,
                spill_volume_threshold: editingConfig.spill_volume_threshold,
            };

            if (editingConfig.id) {
                await updateMutation.mutateAsync({
                    projectId,
                    configId: editingConfig.id,
                    update: configData,
                });
            } else {
                await createMutation.mutateAsync({
                    projectId,
                    config: configData,
                });
            }
            setEditingConfig(null);
        } catch (error) {
            console.error('Failed to save config:', error);
        }
    };

    const deleteConfig = async (config: AnalysisConfigDB) => {
        if (!confirm(`Delete configuration "${config.name}"?`)) return;
        try {
            await deleteMutation.mutateAsync({ projectId, configId: config.id });
        } catch (error) {
            console.error('Failed to delete config:', error);
        }
    };

    if (isLoading) {
        return (
            <div className="flex justify-center items-center h-32">
                <Loader2 className="animate-spin text-orange-500" size={24} />
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {/* Info banner if no date range */}
            {!hasDateRange && (
                <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 flex items-start gap-3">
                    <AlertTriangle className="text-amber-500 flex-shrink-0 mt-0.5" size={20} />
                    <div>
                        <p className="text-amber-800 font-medium">No data uploaded</p>
                        <p className="text-amber-600 text-sm">
                            Upload CSV data files in the Data Import tab first to enable date constraints.
                        </p>
                    </div>
                </div>
            )}

            {/* Date range info */}
            {hasDateRange && (
                <div className="bg-blue-50 border border-blue-200 rounded-lg px-4 py-2 text-sm text-blue-700">
                    📅 Data available: {new Date(dateRange!.min_date!).toLocaleDateString()} – {new Date(dateRange!.max_date!).toLocaleDateString()}
                </div>
            )}

            {/* Add button */}
            <div className="flex justify-between items-center">
                <p className="text-sm text-gray-500">
                    {configs?.length || 0} configuration{configs?.length !== 1 ? 's' : ''} defined
                </p>
                <button
                    onClick={startNewConfig}
                    disabled={!!editingConfig}
                    className="bg-orange-600 text-white px-4 py-2 rounded-lg hover:bg-orange-700 transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 font-medium"
                >
                    <Plus size={18} />
                    Add Configuration
                </button>
            </div>

            {/* New/Edit form card */}
            {editingConfig && (
                <div className="bg-orange-50 border-2 border-orange-300 rounded-xl p-5">
                    <h3 className="text-lg font-semibold text-orange-800 mb-4">
                        {editingConfig.id ? 'Edit Configuration' : 'New Configuration'}
                    </h3>
                    <div className="space-y-4">
                        {/* Name */}
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Configuration Name *</label>
                            <input
                                type="text"
                                value={editingConfig.name}
                                onChange={(e) => setEditingConfig({ ...editingConfig, name: e.target.value })}
                                className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-orange-500 focus:border-orange-500"
                                placeholder="e.g. 10 SPA Assessment"
                            />
                        </div>

                        {/* Mode and Model */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Mode *</label>
                                <select
                                    value={editingConfig.mode}
                                    onChange={(e) => setEditingConfig({ ...editingConfig, mode: e.target.value })}
                                    className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-orange-500 focus:border-orange-500"
                                >
                                    {MODES.map((mode) => (
                                        <option key={mode} value={mode}>{mode}</option>
                                    ))}
                                </select>
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Model *</label>
                                <select
                                    value={editingConfig.model}
                                    onChange={(e) => {
                                        const model = parseInt(e.target.value);
                                        setEditingConfig({ ...editingConfig, model });
                                        if (model === 4) setShowAdvanced(true);
                                    }}
                                    className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-orange-500 focus:border-orange-500"
                                >
                                    {Object.entries(MODELS).map(([key, name]) => (
                                        <option key={key} value={key}>{name}</option>
                                    ))}
                                </select>
                            </div>
                        </div>

                        {/* Date Range */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Start Date *</label>
                                <input
                                    type="datetime-local"
                                    value={editingConfig.start_date}
                                    onChange={(e) => setEditingConfig({ ...editingConfig, start_date: e.target.value })}
                                    min={minDate || undefined}
                                    max={maxDate || undefined}
                                    className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-orange-500 focus:border-orange-500"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">End Date *</label>
                                <input
                                    type="datetime-local"
                                    value={editingConfig.end_date}
                                    onChange={(e) => setEditingConfig({ ...editingConfig, end_date: e.target.value })}
                                    min={minDate || undefined}
                                    max={maxDate || undefined}
                                    className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-orange-500 focus:border-orange-500"
                                />
                            </div>
                        </div>

                        {/* Spill Target */}
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">Spill Target (Entire Period) *</label>
                                <div className="flex items-center gap-3">
                                    <input
                                        type="number"
                                        value={editingConfig.spill_target}
                                        onChange={(e) => setEditingConfig({ ...editingConfig, spill_target: parseInt(e.target.value) || 0 })}
                                        className="w-32 border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-orange-500 focus:border-orange-500"
                                    />
                                    {editingConfig.start_date && editingConfig.end_date && (
                                        <span className="text-sm font-medium text-blue-600">
                                            → {(() => {
                                                const start = new Date(editingConfig.start_date);
                                                const end = new Date(editingConfig.end_date);
                                                const years = (end.getTime() - start.getTime()) / (365.25 * 24 * 60 * 60 * 1000);
                                                if (years <= 0) return 'N/A';
                                                const spa = editingConfig.spill_target / years;
                                                return `${spa.toFixed(1)} spills/year`;
                                            })()}
                                        </span>
                                    )}
                                </div>
                            </div>
                            {editingConfig.model === 4 && (
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">Spill Target (Bathing) *</label>
                                    <input
                                        type="number"
                                        value={editingConfig.spill_target_bathing ?? ''}
                                        onChange={(e) => setEditingConfig({ ...editingConfig, spill_target_bathing: e.target.value ? parseInt(e.target.value) : null })}
                                        className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-orange-500 focus:border-orange-500"
                                    />
                                </div>
                            )}
                        </div>

                        {/* Bathing Season (Model 4) */}
                        {editingConfig.model === 4 && (
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 bg-cyan-50 border border-cyan-200 rounded-lg p-4">
                                <div>
                                    <label className="block text-sm font-medium text-cyan-800 mb-1">Bathing Season Start (DD/MM)</label>
                                    <input
                                        type="text"
                                        value={editingConfig.bathing_season_start}
                                        onChange={(e) => setEditingConfig({ ...editingConfig, bathing_season_start: e.target.value })}
                                        placeholder="15/05"
                                        className="w-full border border-cyan-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-cyan-800 mb-1">Bathing Season End (DD/MM)</label>
                                    <input
                                        type="text"
                                        value={editingConfig.bathing_season_end}
                                        onChange={(e) => setEditingConfig({ ...editingConfig, bathing_season_end: e.target.value })}
                                        placeholder="30/09"
                                        className="w-full border border-cyan-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-cyan-500 focus:border-cyan-500"
                                    />
                                </div>
                            </div>
                        )}

                        {/* Advanced Settings Toggle */}
                        <button
                            type="button"
                            onClick={() => setShowAdvanced(!showAdvanced)}
                            className="flex items-center gap-2 text-sm text-gray-600 hover:text-gray-800"
                        >
                            <ChevronDown className={`transform transition ${showAdvanced ? 'rotate-180' : ''}`} size={16} />
                            Advanced Thresholds
                        </button>

                        {showAdvanced && (
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">Spill Flow Threshold (m³/s)</label>
                                    <input
                                        type="number"
                                        step="0.001"
                                        value={editingConfig.spill_flow_threshold}
                                        onChange={(e) => setEditingConfig({ ...editingConfig, spill_flow_threshold: parseFloat(e.target.value) || 0 })}
                                        className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-orange-500 focus:border-orange-500"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">Spill Volume Threshold (m³)</label>
                                    <input
                                        type="number"
                                        step="0.1"
                                        value={editingConfig.spill_volume_threshold}
                                        onChange={(e) => setEditingConfig({ ...editingConfig, spill_volume_threshold: parseFloat(e.target.value) || 0 })}
                                        className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-orange-500 focus:border-orange-500"
                                    />
                                </div>
                            </div>
                        )}

                        <div className="flex gap-3 pt-2">
                            <button
                                onClick={saveConfig}
                                disabled={createMutation.isPending || updateMutation.isPending}
                                className="bg-orange-600 text-white px-4 py-2 rounded-lg hover:bg-orange-700 transition disabled:opacity-50 flex items-center gap-2"
                            >
                                {(createMutation.isPending || updateMutation.isPending) ? (
                                    <Loader2 className="animate-spin" size={16} />
                                ) : (
                                    <CheckCircle size={16} />
                                )}
                                {editingConfig.id ? 'Save Changes' : 'Create Configuration'}
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

            {/* Configuration cards */}
            <div className="space-y-3">
                {configs?.map((config) => (
                    <div
                        key={config.id}
                        className="bg-white border border-gray-200 rounded-xl p-5 hover:border-orange-300 transition"
                    >
                        <div className="flex items-start justify-between">
                            <div className="flex items-center gap-3">
                                <div className="w-10 h-10 bg-orange-100 rounded-lg flex items-center justify-center">
                                    <Settings className="text-orange-600" size={20} />
                                </div>
                                <div>
                                    <h4 className="font-semibold text-gray-900">{config.name}</h4>
                                    <p className="text-xs text-gray-400">{config.mode} • {MODELS[config.model]}</p>
                                </div>
                            </div>
                            <div className="flex gap-2">
                                <button
                                    onClick={() => startEditConfig(config)}
                                    disabled={!!editingConfig}
                                    className="p-2 text-gray-400 hover:text-orange-600 hover:bg-orange-50 rounded-lg transition disabled:opacity-50"
                                    title="Edit"
                                >
                                    <Edit2 size={16} />
                                </button>
                                <button
                                    onClick={() => deleteConfig(config)}
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
                                    <Calendar size={14} /> Period
                                </p>
                                <span className="font-medium text-gray-900">
                                    {new Date(config.start_date).toLocaleDateString()} - {new Date(config.end_date).toLocaleDateString()}
                                </span>
                            </div>
                            <div>
                                <p className="text-gray-500 mb-1 flex items-center gap-1">
                                    <Target size={14} /> Spill Target
                                </p>
                                <span className="font-medium text-gray-900">
                                    {config.spill_target} spills
                                    <span className="text-blue-600 ml-1">
                                        ({(() => {
                                            const start = new Date(config.start_date);
                                            const end = new Date(config.end_date);
                                            const years = (end.getTime() - start.getTime()) / (365.25 * 24 * 60 * 60 * 1000);
                                            if (years <= 0) return 'N/A';
                                            return (config.spill_target / years).toFixed(1);
                                        })()} SPA)
                                    </span>
                                </span>
                            </div>
                            {config.model === 4 && config.spill_target_bathing !== null && (
                                <div>
                                    <p className="text-gray-500 mb-1">Bathing Target</p>
                                    <span className="font-medium text-cyan-700">{config.spill_target_bathing} spills</span>
                                </div>
                            )}
                            <div>
                                <p className="text-gray-500 mb-1">Flow Threshold</p>
                                <span className="font-medium text-gray-900">{config.spill_flow_threshold} m³/s</span>
                            </div>
                        </div>
                    </div>
                ))}
            </div>

            {(!configs || configs.length === 0) && !editingConfig && (
                <div className="text-center py-12 text-gray-400">
                    <Settings size={48} className="mx-auto mb-4 opacity-50" />
                    <p>No analysis configurations defined yet</p>
                    <p className="text-sm mt-2">Click "Add Configuration" to create one.</p>
                </div>
            )}
        </div>
    );
};

export default AnalysisConfigsTab;
