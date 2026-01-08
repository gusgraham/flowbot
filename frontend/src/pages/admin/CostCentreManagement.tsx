import { useState } from 'react';
import {
    useCostCentres, useCreateCostCentre, useUpdateCostCentre, useDeleteCostCentre,
    useModuleWeights, useUpdateModuleWeight, useBudgets, useCreateBudget,
    useUpdateBudget, useDeleteBudget,
    useInvoices, useGenerateInvoices, useCreateStorageSnapshot
} from '../../api/hooks';
import type {
    CostCentre, CostCentreCreate, BudgetConfigCreate, MonthlyInvoice
} from '../../api/hooks';
import {
    Plus, Edit2, Trash2, Building2, X, Check, FileText, Database, RefreshCw,
    Scale, DollarSign, Download as DownloadIcon
} from 'lucide-react';

type TabType = 'cost-centres' | 'module-weights' | 'budgets' | 'invoices';

const CostCentreManagement = () => {
    const [activeTab, setActiveTab] = useState<TabType>('cost-centres');

    return (
        <div className="p-6 max-w-7xl mx-auto">
            <div className="mb-8">
                <h1 className="text-2xl font-bold text-gray-800 mb-2">Cost Management</h1>
                <p className="text-gray-500">Manage cost centres, module weights, budgets, and invoices</p>
            </div>

            {/* Tabs */}
            <div className="flex gap-2 mb-6 border-b border-gray-700">
                <button
                    onClick={() => setActiveTab('cost-centres')}
                    className={`px-4 py-3 flex items-center gap-2 border-b-2 transition-colors ${activeTab === 'cost-centres'
                        ? 'border-blue-500 text-blue-600 font-bold'
                        : 'border-transparent text-gray-500 hover:text-gray-700'
                        }`}
                >
                    <Building2 size={18} />
                    Cost Centres
                </button>
                <button
                    onClick={() => setActiveTab('module-weights')}
                    className={`px-4 py-3 flex items-center gap-2 border-b-2 transition-colors ${activeTab === 'module-weights'
                        ? 'border-blue-500 text-blue-600 font-bold'
                        : 'border-transparent text-gray-500 hover:text-gray-700'
                        }`}
                >
                    <Scale size={18} />
                    Module Weights
                </button>
                <button
                    onClick={() => setActiveTab('budgets')}
                    className={`px-4 py-3 flex items-center gap-2 border-b-2 transition-colors ${activeTab === 'budgets'
                        ? 'border-blue-500 text-blue-600 font-bold'
                        : 'border-transparent text-gray-500 hover:text-gray-700'
                        }`}
                >
                    <DollarSign size={18} />
                    Budgets
                </button>
                <button
                    onClick={() => setActiveTab('invoices')}
                    className={`px-4 py-3 flex items-center gap-2 border-b-2 transition-colors ${activeTab === 'invoices'
                        ? 'border-blue-500 text-blue-600 font-bold'
                        : 'border-transparent text-gray-500 hover:text-gray-700'
                        }`}
                >
                    <FileText size={18} />
                    Invoices
                </button>
            </div>

            {/* Tab Content */}
            {activeTab === 'cost-centres' && <CostCentresTab />}
            {activeTab === 'module-weights' && <ModuleWeightsTab />}
            {activeTab === 'budgets' && <BudgetsTab />}
            {activeTab === 'invoices' && <InvoicesTab />}
        </div>
    );
};

// ==========================================
// COST CENTRES TAB
// ==========================================

const CostCentresTab = () => {
    const { data: costCentres, isLoading, error } = useCostCentres();
    const createCostCentre = useCreateCostCentre();
    const updateCostCentre = useUpdateCostCentre();
    const deleteCostCentre = useDeleteCostCentre();

    const [isAddModalOpen, setIsAddModalOpen] = useState(false);
    const [editingId, setEditingId] = useState<number | null>(null);
    const [formData, setFormData] = useState<CostCentreCreate>({ name: '', code: '', is_overhead: false });

    const handleAdd = async () => {
        try {
            await createCostCentre.mutateAsync(formData);
            setIsAddModalOpen(false);
            setFormData({ name: '', code: '', is_overhead: false });
        } catch (err: any) {
            alert(err.response?.data?.detail || 'Failed to create cost centre');
        }
    };

    const handleUpdate = async (id: number) => {
        try {
            await updateCostCentre.mutateAsync({ id, updates: formData });
            setEditingId(null);
            setFormData({ name: '', code: '', is_overhead: false });
        } catch (err: any) {
            alert(err.response?.data?.detail || 'Failed to update cost centre');
        }
    };

    const handleDelete = async (cc: CostCentre) => {
        if (confirm(`Delete cost centre "${cc.name}"? Users assigned to it will be unassigned.`)) {
            try {
                await deleteCostCentre.mutateAsync(cc.id);
            } catch (err: any) {
                alert(err.response?.data?.detail || 'Failed to delete cost centre');
            }
        }
    };

    const startEdit = (cc: CostCentre) => {
        setEditingId(cc.id);
        setFormData({ name: cc.name, code: cc.code, is_overhead: cc.is_overhead });
    };

    if (isLoading) return <div className="text-gray-400">Loading cost centres...</div>;
    if (error) return <div className="text-red-400">Error loading cost centres</div>;

    return (
        <div>
            <div className="flex justify-end mb-4">
                <button
                    onClick={() => setIsAddModalOpen(true)}
                    className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg transition-colors"
                >
                    <Plus size={18} />
                    Add Cost Centre
                </button>
            </div>

            <div className="bg-white rounded-xl border border-gray-200 overflow-hidden shadow-sm">
                <table className="w-full text-left">
                    <thead className="bg-gray-50 text-gray-500 text-xs uppercase letter-spacing-wider">
                        <tr>
                            <th className="px-6 py-4 font-semibold">Name</th>
                            <th className="px-6 py-4 font-semibold">Code</th>
                            <th className="px-6 py-4 font-semibold">Type</th>
                            <th className="px-6 py-4 font-semibold">Created</th>
                            <th className="px-6 py-4 font-semibold text-right">Actions</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                        {costCentres?.map((cc) => (
                            <tr key={cc.id} className="hover:bg-gray-50 transition-colors">
                                <td className="px-6 py-4 text-sm">
                                    {editingId === cc.id ? (
                                        <input
                                            type="text"
                                            value={formData.name}
                                            onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                            className="bg-white border border-gray-300 rounded px-2 py-1 text-gray-900 focus:ring-2 focus:ring-blue-500 outline-none w-full"
                                        />
                                    ) : (
                                        <span className="text-gray-900 font-medium">{cc.name}</span>
                                    )}
                                </td>
                                <td className="px-6 py-4 text-sm">
                                    {editingId === cc.id ? (
                                        <input
                                            type="text"
                                            value={formData.code}
                                            onChange={(e) => setFormData({ ...formData, code: e.target.value })}
                                            className="bg-white border border-gray-300 rounded px-2 py-1 text-gray-900 focus:ring-2 focus:ring-blue-500 outline-none w-28"
                                        />
                                    ) : (
                                        <span className="px-3 py-1 rounded-full text-xs font-semibold bg-blue-50 text-blue-700 border border-blue-100">
                                            {cc.code}
                                        </span>
                                    )}
                                </td>
                                <td className="px-6 py-4 text-sm">
                                    {cc.is_overhead ? (
                                        <span className="px-3 py-1 rounded-full text-xs font-semibold bg-amber-50 text-amber-700 border border-amber-100">
                                            Overhead
                                        </span>
                                    ) : (
                                        <span className="px-3 py-1 rounded-full text-xs font-semibold bg-green-50 text-green-700 border border-green-100">
                                            Department
                                        </span>
                                    )}
                                </td>
                                <td className="px-6 py-4 text-gray-500 text-sm">
                                    {new Date(cc.created_at).toLocaleDateString()}
                                </td>
                                <td className="px-6 py-4 text-right">
                                    {editingId === cc.id ? (
                                        <div className="flex gap-1 justify-end">
                                            <button
                                                onClick={() => handleUpdate(cc.id)}
                                                className="p-2 hover:bg-green-50 rounded-lg text-green-600 transition-colors"
                                                title="Save"
                                            >
                                                <Check size={18} />
                                            </button>
                                            <button
                                                onClick={() => setEditingId(null)}
                                                className="p-2 hover:bg-gray-100 rounded-lg text-gray-500 transition-colors"
                                                title="Cancel"
                                            >
                                                <X size={18} />
                                            </button>
                                        </div>
                                    ) : (
                                        <div className="flex gap-1 justify-end">
                                            <button
                                                onClick={() => startEdit(cc)}
                                                className="p-2 hover:bg-gray-100 rounded-lg text-gray-500 hover:text-blue-600 transition-colors"
                                                title="Edit"
                                            >
                                                <Edit2 size={18} />
                                            </button>
                                            <button
                                                onClick={() => handleDelete(cc)}
                                                className="p-2 hover:bg-red-50 rounded-lg text-gray-500 hover:text-red-600 transition-colors"
                                                title="Delete"
                                            >
                                                <Trash2 size={18} />
                                            </button>
                                        </div>
                                    )}
                                </td>
                            </tr>
                        ))}
                        {(!costCentres || costCentres.length === 0) && (
                            <tr>
                                <td colSpan={5} className="px-6 py-12 text-center text-gray-500">
                                    <Building2 className="mx-auto mb-2 text-gray-300" size={32} />
                                    <p>No cost centres defined.</p>
                                    <p className="text-xs">Click "Add Cost Centre" to create one.</p>
                                </td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>

            {isAddModalOpen && (
                <div className="fixed inset-0 bg-gray-900/40 backdrop-blur-sm flex items-center justify-center z-50">
                    <div className="bg-white rounded-xl border border-gray-200 p-8 w-full max-w-md shadow-xl">
                        <h2 className="text-xl font-bold text-gray-800 mb-6">Add Cost Centre</h2>
                        <div className="space-y-4">
                            <div>
                                <label className="block text-sm font-semibold text-gray-600 mb-1">Name</label>
                                <input
                                    type="text"
                                    value={formData.name}
                                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                    placeholder="e.g., Engineering"
                                    className="w-full bg-white border border-gray-300 rounded-lg px-4 py-2 text-gray-900 focus:ring-2 focus:ring-blue-500 outline-none"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-semibold text-gray-600 mb-1">Code</label>
                                <input
                                    type="text"
                                    value={formData.code}
                                    onChange={(e) => setFormData({ ...formData, code: e.target.value.toUpperCase() })}
                                    placeholder="e.g., ENG-001"
                                    className="w-full bg-white border border-gray-300 rounded-lg px-4 py-2 text-gray-900 focus:ring-2 focus:ring-blue-500 outline-none"
                                />
                            </div>
                            <div className="flex items-center gap-3">
                                <input
                                    type="checkbox"
                                    id="is_overhead"
                                    checked={formData.is_overhead ?? false}
                                    onChange={(e) => setFormData({ ...formData, is_overhead: e.target.checked })}
                                    className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                                />
                                <label htmlFor="is_overhead" className="text-sm text-gray-600">
                                    Overhead (costs distributed pro-rata to other centres)
                                </label>
                            </div>
                        </div>
                        <div className="flex justify-end gap-3 mt-8">
                            <button
                                onClick={() => setIsAddModalOpen(false)}
                                className="px-4 py-2 text-gray-500 hover:text-gray-700 font-medium transition-colors"
                            >
                                Cancel
                            </button>
                            <button
                                onClick={handleAdd}
                                disabled={!formData.name || !formData.code}
                                className="px-6 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-200 disabled:text-gray-400 disabled:cursor-not-allowed text-white font-semibold rounded-lg shadow-sm transition-all"
                            >
                                Create
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

// ==========================================
// MODULE WEIGHTS TAB
// ==========================================

const ModuleWeightsTab = () => {
    const { data: weights, isLoading, error } = useModuleWeights();
    const updateWeight = useUpdateModuleWeight();
    const [editingId, setEditingId] = useState<number | null>(null);
    const [editValue, setEditValue] = useState<number>(1.0);

    const handleSave = async (id: number) => {
        try {
            await updateWeight.mutateAsync({ id, updates: { weight: editValue } });
            setEditingId(null);
        } catch (err: any) {
            alert(err.response?.data?.detail || 'Failed to update weight');
        }
    };

    if (isLoading) return <div className="text-gray-400">Loading module weights...</div>;
    if (error) return <div className="text-red-400">Error loading module weights</div>;

    return (
        <div>
            <p className="text-gray-500 mb-6">
                Adjust the relative weight of each module for usage-based cost allocation.
                Higher weights mean more cost is attributed to that module's usage.
            </p>

            <div className="bg-white rounded-xl border border-gray-200 overflow-hidden shadow-sm">
                <table className="w-full text-left">
                    <thead className="bg-gray-50 text-gray-500 text-xs uppercase letter-spacing-wider">
                        <tr>
                            <th className="px-6 py-4 font-semibold">Module</th>
                            <th className="px-6 py-4 font-semibold">Description</th>
                            <th className="px-6 py-4 font-semibold">Weight</th>
                            <th className="px-6 py-4 font-semibold text-right">Actions</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                        {weights?.map((w) => (
                            <tr key={w.id} className="hover:bg-gray-700/30 transition-colors">
                                <td className="px-6 py-4">
                                    <span className="px-3 py-1 rounded-full text-xs font-semibold bg-blue-50 text-blue-700 border border-blue-100">
                                        {w.module}
                                    </span>
                                </td>
                                <td className="px-6 py-4 text-gray-600">{w.description || '-'}</td>
                                <td className="px-6 py-4">
                                    {editingId === w.id ? (
                                        <input
                                            type="number"
                                            step="0.1"
                                            min="0"
                                            value={editValue}
                                            onChange={(e) => setEditValue(parseFloat(e.target.value))}
                                            className="bg-white border border-gray-300 rounded px-2 py-1 text-gray-900 w-20 focus:ring-2 focus:ring-blue-500 outline-none"
                                        />
                                    ) : (
                                        <span className="text-gray-900 font-mono font-medium">{w.weight.toFixed(1)}</span>
                                    )}
                                </td>
                                <td className="px-6 py-4 text-right">
                                    {editingId === w.id ? (
                                        <div className="flex gap-1 justify-end">
                                            <button
                                                onClick={() => handleSave(w.id)}
                                                className="p-2 hover:bg-green-50 rounded-lg text-green-600 transition-colors"
                                            >
                                                <Check size={18} />
                                            </button>
                                            <button
                                                onClick={() => setEditingId(null)}
                                                className="p-2 hover:bg-gray-100 rounded-lg text-gray-500 transition-colors"
                                            >
                                                <X size={18} />
                                            </button>
                                        </div>
                                    ) : (
                                        <button
                                            onClick={() => { setEditingId(w.id); setEditValue(w.weight); }}
                                            className="p-2 hover:bg-gray-100 rounded-lg text-gray-500 hover:text-blue-600 transition-colors"
                                        >
                                            <Edit2 size={18} />
                                        </button>
                                    )}
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

// ==========================================
// BUDGETS TAB
// ==========================================

const BudgetsTab = () => {
    const { data: budgets, isLoading, error } = useBudgets();
    const createBudget = useCreateBudget();
    const updateBudget = useUpdateBudget();
    const deleteBudget = useDeleteBudget();

    const [isModalOpen, setIsModalOpen] = useState(false);
    const [editingId, setEditingId] = useState<number | null>(null);
    const [formData, setFormData] = useState<BudgetConfigCreate>({
        effective_date: new Date().toISOString().split('T')[0],
        hosting_budget: 0,
        development_budget: 0,
        storage_weight_pct: 30,
        notes: '',
    });

    const handleOpenCreate = () => {
        setEditingId(null);
        setFormData({
            effective_date: new Date().toISOString().split('T')[0],
            hosting_budget: 0,
            development_budget: 0,
            storage_weight_pct: 30,
            notes: '',
        });
        setIsModalOpen(true);
    };

    const handleOpenEdit = (budget: any) => {
        setEditingId(budget.id);
        setFormData({
            effective_date: budget.effective_date,
            hosting_budget: budget.hosting_budget,
            development_budget: budget.development_budget,
            storage_weight_pct: budget.storage_weight_pct,
            notes: budget.notes || '',
        });
        setIsModalOpen(true);
    };

    const handleSubmit = async () => {
        try {
            if (editingId) {
                await updateBudget.mutateAsync({ id: editingId, updates: formData });
            } else {
                await createBudget.mutateAsync(formData);
            }
            setIsModalOpen(false);
        } catch (err: any) {
            alert(err.response?.data?.detail || `Failed to ${editingId ? 'update' : 'create'} budget`);
        }
    };

    const handleDelete = async (id: number) => {
        if (confirm("Are you sure you want to delete this budget configuration?")) {
            try {
                await deleteBudget.mutateAsync(id);
            } catch (err: any) {
                alert(err.response?.data?.detail || 'Failed to delete budget');
            }
        }
    };

    if (isLoading) return <div className="text-gray-400">Loading budgets...</div>;
    if (error) return <div className="text-red-400">Error loading budgets</div>;

    return (
        <div>
            <div className="flex justify-end mb-4">
                <button
                    onClick={handleOpenCreate}
                    className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg transition-colors"
                >
                    <Plus size={18} />
                    Add Budget
                </button>
            </div>

            <div className="bg-white rounded-xl border border-gray-200 overflow-hidden shadow-sm">
                <table className="w-full text-left">
                    <thead className="bg-gray-50 text-gray-500 text-xs uppercase letter-spacing-wider">
                        <tr>
                            <th className="px-6 py-4 font-semibold">Effective Date</th>
                            <th className="px-6 py-4 font-semibold">Hosting</th>
                            <th className="px-6 py-4 font-semibold">Development</th>
                            <th className="px-6 py-4 font-semibold">Total</th>
                            <th className="px-6 py-4 font-semibold">Storage %</th>
                            <th className="px-6 py-4 font-semibold">Notes</th>
                            <th className="px-6 py-4 font-semibold text-right">Actions</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                        {budgets?.map((b, idx) => (
                            <tr key={b.id} className={`hover:bg-gray-50 transition-colors ${idx === 0 ? 'bg-green-50/50' : ''}`}>
                                <td className="px-6 py-4">
                                    <span className="text-gray-900 font-medium">{b.effective_date}</span>
                                    {idx === 0 && <span className="ml-2 text-xs font-bold text-green-600 uppercase tracking-tight">(Current)</span>}
                                </td>
                                <td className="px-6 py-4 text-gray-600 font-mono">£{b.hosting_budget.toFixed(2)}</td>
                                <td className="px-6 py-4 text-gray-600 font-mono">£{b.development_budget.toFixed(2)}</td>
                                <td className="px-6 py-4 text-gray-900 font-semibold font-mono">£{(b.hosting_budget + b.development_budget).toFixed(2)}</td>
                                <td className="px-6 py-4 text-gray-600">{b.storage_weight_pct}%</td>
                                <td className="px-6 py-4 text-gray-500 text-sm">{b.notes || '-'}</td>
                                <td className="px-6 py-4 text-right">
                                    <div className="flex gap-1 justify-end">
                                        <button
                                            onClick={() => handleOpenEdit(b)}
                                            className="p-2 hover:bg-gray-100 rounded-lg text-gray-500 hover:text-blue-600 transition-colors"
                                            title="Edit"
                                        >
                                            <Edit2 size={18} />
                                        </button>
                                        <button
                                            onClick={() => handleDelete(b.id)}
                                            className="p-2 hover:bg-red-50 rounded-lg text-gray-500 hover:text-red-600 transition-colors"
                                            title="Delete"
                                        >
                                            <Trash2 size={18} />
                                        </button>
                                    </div>
                                </td>
                            </tr>
                        ))}
                        {(!budgets || budgets.length === 0) && (
                            <tr>
                                <td colSpan={7} className="px-6 py-8 text-center text-gray-500">
                                    No budgets defined. Click "Add Budget" to create one.
                                </td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>

            {isModalOpen && (
                <div className="fixed inset-0 bg-gray-900/40 backdrop-blur-sm flex items-center justify-center z-50">
                    <div className="bg-white rounded-xl border border-gray-200 p-8 w-full max-w-md shadow-xl">
                        <h2 className="text-xl font-bold text-gray-800 mb-6">{editingId ? 'Edit Budget Config' : 'Add Budget Config'}</h2>
                        <div className="space-y-4">
                            <div>
                                <label className="block text-sm font-semibold text-gray-600 mb-1">Effective Date</label>
                                <input
                                    type="date"
                                    value={formData.effective_date}
                                    onChange={(e) => setFormData({ ...formData, effective_date: e.target.value })}
                                    className="w-full bg-white border border-gray-300 rounded-lg px-4 py-2 text-gray-900 focus:ring-2 focus:ring-blue-500 outline-none"
                                />
                            </div>
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-semibold text-gray-600 mb-1">Hosting (£/month)</label>
                                    <input
                                        type="number"
                                        step="0.01"
                                        value={formData.hosting_budget}
                                        onChange={(e) => setFormData({ ...formData, hosting_budget: parseFloat(e.target.value) || 0 })}
                                        className="w-full bg-white border border-gray-300 rounded-lg px-4 py-2 text-gray-900 focus:ring-2 focus:ring-blue-500 outline-none"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-semibold text-gray-600 mb-1">Development (£/month)</label>
                                    <input
                                        type="number"
                                        step="0.01"
                                        value={formData.development_budget}
                                        onChange={(e) => setFormData({ ...formData, development_budget: parseFloat(e.target.value) || 0 })}
                                        className="w-full bg-white border border-gray-300 rounded-lg px-4 py-2 text-gray-900 focus:ring-2 focus:ring-blue-500 outline-none"
                                    />
                                </div>
                            </div>
                            <div>
                                <label className="block text-sm font-semibold text-gray-600 mb-1">Storage Weight %</label>
                                <input
                                    type="number"
                                    min="0"
                                    max="100"
                                    value={formData.storage_weight_pct}
                                    onChange={(e) => setFormData({ ...formData, storage_weight_pct: parseInt(e.target.value) || 0 })}
                                    className="w-full bg-white border border-gray-300 rounded-lg px-4 py-2 text-gray-900 focus:ring-2 focus:ring-blue-500 outline-none"
                                />
                                <p className="text-xs text-gray-500 mt-1">% of total cost based on storage (remainder is utilization)</p>
                            </div>
                            <div>
                                <label className="block text-sm font-semibold text-gray-600 mb-1">Notes</label>
                                <input
                                    type="text"
                                    value={formData.notes || ''}
                                    onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                                    placeholder="e.g., Q1 2026 budget increase"
                                    className="w-full bg-white border border-gray-300 rounded-lg px-4 py-2 text-gray-900 focus:ring-2 focus:ring-blue-500 outline-none"
                                />
                            </div>
                        </div>
                        <div className="flex justify-end gap-3 mt-8">
                            <button
                                onClick={() => setIsModalOpen(false)}
                                className="px-4 py-2 text-gray-500 hover:text-gray-700 font-medium transition-colors"
                            >
                                Cancel
                            </button>
                            <button
                                onClick={handleSubmit}
                                className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg shadow-sm transition-all"
                            >
                                {editingId ? 'Update' : 'Create'}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

// ==========================================
// INVOICES TAB
// ==========================================

const InvoicesTab = () => {
    const [selectedMonth, setSelectedMonth] = useState(new Date().toISOString().substring(0, 7));
    const { data: invoices, isLoading, error, refetch } = useInvoices({ year_month: selectedMonth });
    const { data: costCentres } = useCostCentres();
    const generateInvoices = useGenerateInvoices();
    const takeSnapshot = useCreateStorageSnapshot();
    const [isGenerating, setIsGenerating] = useState(false);

    const handleGenerate = async () => {
        if (!confirm(`Generate invoices for ${selectedMonth}? This will overwrite existing invoices for this month.`)) return;

        setIsGenerating(true);
        try {
            await generateInvoices.mutateAsync(selectedMonth);
            refetch();
        } catch (err: any) {
            alert(err.response?.data?.detail || 'Failed to generate invoices');
        } finally {
            setIsGenerating(false);
        }
    };

    const handleSnapshot = async () => {
        try {
            await takeSnapshot.mutateAsync();
            alert('Storage snapshot captured successfully.');
        } catch (err: any) {
            alert(err.response?.data?.detail || 'Failed to capture snapshot');
        }
    };

    // Add PDF handling
    const handleDownloadPdf = async (invoiceId: number) => {
        try {
            // Using direct fetch blob for file download helper
            const token = localStorage.getItem('token');
            const response = await fetch(`${import.meta.env.VITE_API_URL || '/api'}/admin/invoices/${invoiceId}/pdf`, {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (!response.ok) throw new Error('Download failed');

            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            // Extract filename or default
            const disposition = response.headers.get('content-disposition');
            let filename = 'invoice.pdf';
            if (disposition && disposition.indexOf('filename=') !== -1) {
                const matches = /filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/.exec(disposition);
                if (matches != null && matches[1]) {
                    filename = matches[1].replace(/['"]/g, '');
                }
            }
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        } catch (err) {
            console.error(err);
            alert("Failed to download PDF");
        }
    };

    if (isLoading) return <div className="text-gray-600 py-12 text-center">Loading invoices...</div>;
    if (error) return <div className="text-red-600 py-12 text-center font-medium">Error loading invoices</div>;

    const totalInvoiced = invoices?.reduce((sum: number, inv: MonthlyInvoice) => sum + inv.total_cost, 0) || 0;

    return (
        <div>
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-8">
                <div className="flex items-center gap-3 bg-white p-1 rounded-lg border border-gray-200 shadow-sm">
                    <input
                        type="month"
                        value={selectedMonth}
                        onChange={(e) => setSelectedMonth(e.target.value)}
                        className="bg-transparent border-none text-gray-900 font-bold focus:ring-0 cursor-pointer px-3"
                    />
                </div>

                <div className="flex gap-2">
                    <button
                        onClick={handleSnapshot}
                        className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 hover:bg-gray-50 text-gray-700 font-semibold rounded-lg shadow-sm transition-all"
                    >
                        <Database size={18} />
                        Capture Storage Snapshot
                    </button>
                    <button
                        onClick={handleGenerate}
                        disabled={isGenerating}
                        className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg shadow-sm transition-all disabled:opacity-50"
                    >
                        {isGenerating ? 'Generating...' : (
                            <>
                                <RefreshCw size={18} className={isGenerating ? 'animate-spin' : ''} />
                                Generate Invoices
                            </>
                        )}
                    </button>
                </div>
            </div>

            {invoices && invoices.length > 0 && (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                    <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
                        <p className="text-sm font-semibold text-gray-500 uppercase mb-1">Total Allocated</p>
                        <p className="text-3xl font-bold text-gray-900">£{totalInvoiced.toLocaleString(undefined, { minimumFractionDigits: 2 })}</p>
                    </div>
                    <div className="bg-white p-6 rounded-xl border border-gray-200 shadow-sm">
                        <p className="text-sm font-semibold text-gray-500 uppercase mb-1">Active Centres</p>
                        <p className="text-3xl font-bold text-blue-600">{invoices.length}</p>
                    </div>
                </div>
            )}

            <div className="bg-white rounded-xl border border-gray-200 overflow-hidden shadow-sm">
                <table className="w-full text-left">
                    <thead className="bg-gray-50 text-gray-500 text-xs uppercase letter-spacing-wider">
                        <tr>
                            <th className="px-6 py-4 font-semibold">Cost Centre</th>
                            <th className="px-6 py-4 font-semibold">Share %</th>
                            <th className="px-6 py-4 font-semibold">Utilization</th>
                            <th className="px-6 py-4 font-semibold">Storage</th>
                            <th className="px-6 py-4 font-semibold text-right">Total Cost</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                        {invoices?.map((inv: MonthlyInvoice) => {
                            const cc = costCentres?.find(c => c.id === inv.cost_centre_id);
                            return (
                                <tr key={inv.id} className="hover:bg-gray-50 transition-colors">
                                    <td className="px-6 py-4">
                                        <div className="flex flex-col">
                                            <span className="text-gray-900 font-semibold">{cc ? cc.name : `CC-${inv.cost_centre_id}`}</span>
                                            {cc && <span className="text-xs text-gray-500">{cc.code}</span>}
                                        </div>
                                    </td>
                                    <td className="px-6 py-4">
                                        <div className="flex items-center gap-2">
                                            <div className="w-16 h-2 bg-gray-100 rounded-full overflow-hidden">
                                                <div
                                                    className="h-full bg-blue-500"
                                                    style={{ width: `${Math.min(100, inv.share_pct)}%` }}
                                                />
                                            </div>
                                            <span className="text-gray-900 font-medium">{inv.share_pct.toFixed(1)}%</span>
                                        </div>
                                    </td>
                                    <td className="px-6 py-4 text-gray-600 font-mono">£{inv.utilization_cost.toFixed(2)}</td>
                                    <td className="px-6 py-4 text-gray-600 font-mono">£{inv.storage_cost.toFixed(2)}</td>
                                    <td className="px-6 py-4 text-right">
                                        <div className="flex flex-col items-end gap-1">
                                            <span className="text-gray-900 font-bold font-mono">£{inv.total_cost.toFixed(2)}</span>
                                            <button
                                                onClick={() => handleDownloadPdf(inv.id)}
                                                className="flex items-center gap-1 text-xs text-blue-600 hover:text-blue-800 hover:underline"
                                            >
                                                <DownloadIcon size={12} />
                                                PDF
                                            </button>
                                        </div>
                                    </td>
                                </tr>
                            );
                        })}
                        {(!invoices || invoices.length === 0) && (
                            <tr>
                                <td colSpan={5} className="px-6 py-12 text-center text-gray-500">
                                    <FileText className="mx-auto mb-2 text-gray-300" size={32} />
                                    <p>No invoices found for {selectedMonth}.</p>
                                    <p className="text-xs">Select a month or click "Generate Invoices" to create them.</p>
                                </td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

export default CostCentreManagement;
