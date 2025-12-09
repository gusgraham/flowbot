import React, { useState } from 'react';
import { Plus, Edit2, Trash2, Container, Loader2, AlertTriangle, Link2, CheckCircle, X } from 'lucide-react';
import {
    useSSDLinks, useSSDCSOAssets, useCreateCSOAsset, useUpdateCSOAsset, useDeleteCSOAsset,
} from '../../api/hooks';
import type { CSOAsset } from '../../api/hooks';

interface CSOAssetsTabProps {
    projectId: number;
}

interface EditingAsset {
    id?: number;
    name: string;
    overflow_links: string[];
    continuation_link: string;
    is_effective_link: boolean;
    effective_link_components: string[] | null;
}

const CSOAssetsTab: React.FC<CSOAssetsTabProps> = ({ projectId }) => {
    const { data: links, isLoading: linksLoading } = useSSDLinks(projectId);
    const { data: assets, isLoading: assetsLoading } = useSSDCSOAssets(projectId);
    const createMutation = useCreateCSOAsset();
    const updateMutation = useUpdateCSOAsset();
    const deleteMutation = useDeleteCSOAsset();

    const [editingAsset, setEditingAsset] = useState<EditingAsset | null>(null);
    const [showEffectiveLinkModal, setShowEffectiveLinkModal] = useState(false);
    const [effectiveLinkSelection, setEffectiveLinkSelection] = useState<string[]>([]);

    const availableLinks = links || [];
    const hasLinks = availableLinks.length > 0;

    const startNewAsset = () => {
        setEditingAsset({
            name: `CSO_${(assets?.length || 0) + 1}`,
            overflow_links: [],
            continuation_link: '',
            is_effective_link: false,
            effective_link_components: null,
        });
    };

    const startEditAsset = (asset: CSOAsset) => {
        setEditingAsset({
            id: asset.id,
            name: asset.name,
            overflow_links: asset.overflow_links,
            continuation_link: asset.continuation_link,
            is_effective_link: asset.is_effective_link,
            effective_link_components: asset.effective_link_components,
        });
    };

    const cancelEdit = () => {
        setEditingAsset(null);
    };

    const saveAsset = async () => {
        if (!editingAsset) return;

        if (!editingAsset.name.trim()) {
            alert('CSO name is required');
            return;
        }
        if (editingAsset.overflow_links.length === 0) {
            alert('At least one overflow link is required');
            return;
        }
        if (!editingAsset.continuation_link) {
            alert('Continuation link is required');
            return;
        }

        try {
            if (editingAsset.id) {
                // Update existing
                await updateMutation.mutateAsync({
                    projectId,
                    assetId: editingAsset.id,
                    update: {
                        name: editingAsset.name,
                        overflow_links: editingAsset.overflow_links,
                        continuation_link: editingAsset.continuation_link,
                        is_effective_link: editingAsset.is_effective_link,
                        effective_link_components: editingAsset.effective_link_components,
                    },
                });
            } else {
                // Create new
                await createMutation.mutateAsync({
                    projectId,
                    asset: {
                        name: editingAsset.name,
                        overflow_links: editingAsset.overflow_links,
                        continuation_link: editingAsset.continuation_link,
                        is_effective_link: editingAsset.is_effective_link,
                        effective_link_components: editingAsset.effective_link_components,
                    },
                });
            }
            setEditingAsset(null);
        } catch (error) {
            console.error('Failed to save asset:', error);
        }
    };

    const deleteAsset = async (asset: CSOAsset) => {
        if (!confirm(`Delete CSO asset "${asset.name}"?`)) return;
        try {
            await deleteMutation.mutateAsync({ projectId, assetId: asset.id });
        } catch (error) {
            console.error('Failed to delete asset:', error);
        }
    };

    const handleOverflowChange = (value: string) => {
        if (!editingAsset) return;
        if (value === '__EFFECTIVE__') {
            setEffectiveLinkSelection([]);
            setShowEffectiveLinkModal(true);
        } else {
            setEditingAsset({
                ...editingAsset,
                overflow_links: [value],
                is_effective_link: false,
                effective_link_components: null,
            });
        }
    };

    const confirmEffectiveLink = () => {
        if (!editingAsset || effectiveLinkSelection.length < 2) return;
        setEditingAsset({
            ...editingAsset,
            overflow_links: effectiveLinkSelection,
            is_effective_link: true,
            effective_link_components: effectiveLinkSelection,
        });
        setShowEffectiveLinkModal(false);
    };

    if (linksLoading || assetsLoading) {
        return (
            <div className="flex justify-center items-center h-32">
                <Loader2 className="animate-spin text-orange-500" size={24} />
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {/* Info banner if no links */}
            {!hasLinks && (
                <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 flex items-start gap-3">
                    <AlertTriangle className="text-amber-500 flex-shrink-0 mt-0.5" size={20} />
                    <div>
                        <p className="text-amber-800 font-medium">No links available</p>
                        <p className="text-amber-600 text-sm">
                            Upload CSV data files in the Data Import tab first. Link names are extracted from column headers.
                        </p>
                    </div>
                </div>
            )}

            {/* Add button */}
            <div className="flex justify-between items-center">
                <p className="text-sm text-gray-500">
                    {assets?.length || 0} CSO asset{assets?.length !== 1 ? 's' : ''} defined
                </p>
                <button
                    onClick={startNewAsset}
                    disabled={!hasLinks || !!editingAsset}
                    className="bg-orange-600 text-white px-4 py-2 rounded-lg hover:bg-orange-700 transition disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 font-medium"
                >
                    <Plus size={18} />
                    Add CSO Asset
                </button>
            </div>

            {/* New/Edit form card */}
            {editingAsset && (
                <div className="bg-orange-50 border-2 border-orange-300 rounded-xl p-5">
                    <h3 className="text-lg font-semibold text-orange-800 mb-4">
                        {editingAsset.id ? 'Edit CSO Asset' : 'New CSO Asset'}
                    </h3>
                    <div className="space-y-4">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">CSO Name *</label>
                            <input
                                type="text"
                                value={editingAsset.name}
                                onChange={(e) => setEditingAsset({ ...editingAsset, name: e.target.value })}
                                className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-orange-500 focus:border-orange-500"
                                placeholder="e.g. Beech Ave CSO"
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Overflow Link(s) *</label>
                            {editingAsset.is_effective_link && editingAsset.effective_link_components ? (
                                <div className="flex items-center gap-2 flex-wrap">
                                    <span className="text-sm text-gray-600">Effective Link:</span>
                                    {editingAsset.effective_link_components.map((link) => (
                                        <span key={link} className="bg-orange-100 text-orange-700 px-2 py-1 rounded text-sm">
                                            {link}
                                        </span>
                                    ))}
                                    <button
                                        onClick={() => setEditingAsset({
                                            ...editingAsset,
                                            overflow_links: [],
                                            is_effective_link: false,
                                            effective_link_components: null,
                                        })}
                                        className="text-gray-400 hover:text-red-500"
                                    >
                                        <X size={16} />
                                    </button>
                                </div>
                            ) : (
                                <select
                                    value={editingAsset.overflow_links[0] || ''}
                                    onChange={(e) => handleOverflowChange(e.target.value)}
                                    className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-orange-500 focus:border-orange-500"
                                >
                                    <option value="">Select overflow link...</option>
                                    <option value="__EFFECTIVE__">📊 Build Effective Link (combine 2+)...</option>
                                    {availableLinks.map((link) => (
                                        <option key={link} value={link}>{link}</option>
                                    ))}
                                </select>
                            )}
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">Continuation Link *</label>
                            <select
                                value={editingAsset.continuation_link}
                                onChange={(e) => setEditingAsset({ ...editingAsset, continuation_link: e.target.value })}
                                className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-orange-500 focus:border-orange-500"
                            >
                                <option value="">Select continuation link...</option>
                                {availableLinks.map((link) => (
                                    <option key={link} value={link}>{link}</option>
                                ))}
                            </select>
                        </div>

                        <div className="flex gap-3 pt-2">
                            <button
                                onClick={saveAsset}
                                disabled={createMutation.isPending || updateMutation.isPending}
                                className="bg-orange-600 text-white px-4 py-2 rounded-lg hover:bg-orange-700 transition disabled:opacity-50 flex items-center gap-2"
                            >
                                {(createMutation.isPending || updateMutation.isPending) ? (
                                    <Loader2 className="animate-spin" size={16} />
                                ) : (
                                    <CheckCircle size={16} />
                                )}
                                {editingAsset.id ? 'Save Changes' : 'Create Asset'}
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

            {/* Asset cards */}
            <div className="space-y-3">
                {assets?.map((asset) => (
                    <div
                        key={asset.id}
                        className="bg-white border border-gray-200 rounded-xl p-5 hover:border-orange-300 transition"
                    >
                        <div className="flex items-start justify-between">
                            <div className="flex items-center gap-3">
                                <div className="w-10 h-10 bg-orange-100 rounded-lg flex items-center justify-center">
                                    <Container className="text-orange-600" size={20} />
                                </div>
                                <div>
                                    <h4 className="font-semibold text-gray-900">{asset.name}</h4>
                                    <p className="text-xs text-gray-400">Created {new Date(asset.created_at).toLocaleDateString()}</p>
                                </div>
                            </div>
                            <div className="flex gap-2">
                                <button
                                    onClick={() => startEditAsset(asset)}
                                    disabled={!!editingAsset}
                                    className="p-2 text-gray-400 hover:text-orange-600 hover:bg-orange-50 rounded-lg transition disabled:opacity-50"
                                    title="Edit"
                                >
                                    <Edit2 size={16} />
                                </button>
                                <button
                                    onClick={() => deleteAsset(asset)}
                                    disabled={deleteMutation.isPending}
                                    className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition disabled:opacity-50"
                                    title="Delete"
                                >
                                    <Trash2 size={16} />
                                </button>
                            </div>
                        </div>

                        <div className="mt-4 grid grid-cols-2 gap-4 text-sm">
                            <div>
                                <p className="text-gray-500 mb-1 flex items-center gap-1">
                                    <Link2 size={14} /> Overflow
                                </p>
                                {asset.is_effective_link && asset.effective_link_components ? (
                                    <div className="flex flex-wrap gap-1">
                                        {asset.effective_link_components.map((link) => (
                                            <span key={link} className="bg-orange-100 text-orange-700 px-2 py-0.5 rounded text-xs">
                                                {link}
                                            </span>
                                        ))}
                                    </div>
                                ) : (
                                    <span className="font-medium text-gray-900">{asset.overflow_links[0]}</span>
                                )}
                            </div>
                            <div>
                                <p className="text-gray-500 mb-1 flex items-center gap-1">
                                    <Link2 size={14} /> Continuation
                                </p>
                                <span className="font-medium text-gray-900">{asset.continuation_link}</span>
                            </div>
                        </div>
                    </div>
                ))}
            </div>

            {(!assets || assets.length === 0) && !editingAsset && (
                <div className="text-center py-12 text-gray-400">
                    <Container size={48} className="mx-auto mb-4 opacity-50" />
                    <p>No CSO assets defined yet</p>
                    <p className="text-sm mt-2">
                        {hasLinks
                            ? 'Click "Add CSO Asset" to create one.'
                            : 'Upload data files first to get available links.'}
                    </p>
                </div>
            )}

            {/* Effective Link Modal */}
            {showEffectiveLinkModal && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
                    <div className="bg-white rounded-xl shadow-xl max-w-md w-full mx-4 p-6">
                        <h3 className="text-lg font-semibold text-gray-900 mb-2">Build Effective Link</h3>
                        <p className="text-sm text-gray-500 mb-4">
                            Select 2 or more links to combine into a single effective overflow link.
                        </p>

                        <div className="border border-gray-200 rounded-lg max-h-64 overflow-auto mb-4">
                            {availableLinks.map((link) => (
                                <label
                                    key={link}
                                    className="flex items-center gap-3 px-3 py-2 hover:bg-gray-50 cursor-pointer"
                                >
                                    <input
                                        type="checkbox"
                                        checked={effectiveLinkSelection.includes(link)}
                                        onChange={(e) => {
                                            if (e.target.checked) {
                                                setEffectiveLinkSelection([...effectiveLinkSelection, link]);
                                            } else {
                                                setEffectiveLinkSelection(effectiveLinkSelection.filter((l) => l !== link));
                                            }
                                        }}
                                        className="w-4 h-4 text-orange-600 border-gray-300 rounded focus:ring-orange-500"
                                    />
                                    <span className="text-sm text-gray-700">{link}</span>
                                </label>
                            ))}
                        </div>

                        <p className="text-sm text-gray-500 mb-4">
                            Selected: {effectiveLinkSelection.length} link{effectiveLinkSelection.length !== 1 ? 's' : ''}
                        </p>

                        <div className="flex gap-3 justify-end">
                            <button
                                onClick={() => setShowEffectiveLinkModal(false)}
                                className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg transition"
                            >
                                Cancel
                            </button>
                            <button
                                onClick={confirmEffectiveLink}
                                disabled={effectiveLinkSelection.length < 2}
                                className="bg-orange-600 text-white px-4 py-2 rounded-lg hover:bg-orange-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                Confirm ({effectiveLinkSelection.length} links)
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default CSOAssetsTab;
