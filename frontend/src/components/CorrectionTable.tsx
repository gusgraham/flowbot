import React, { useState, useCallback } from 'react';
import { Plus, Trash2 } from 'lucide-react';

type ColumnDef = {
    name: string;
    type: 'datetime' | 'number' | 'text';
    label: string;
    placeholder?: string;
    required?: boolean;
};

type CorrectionRow = {
    [key: string]: string | number | null;
};

interface CorrectionTableProps {
    columns: ColumnDef[];
    data: CorrectionRow[];
    onChange: (data: CorrectionRow[]) => void;
    minRows?: number;
}

const CorrectionTable: React.FC<CorrectionTableProps> = ({
    columns,
    data,
    onChange,
    minRows = 1
}) => {
    const [selectedRows, setSelectedRows] = useState<Set<number>>(new Set());

    // Add a new empty row
    const handleAddRow = useCallback(() => {
        const newRow: CorrectionRow = {};
        columns.forEach(col => {
            newRow[col.name] = col.type === 'number' ? 0 : '';
        });
        onChange([...data, newRow]);
    }, [data, columns, onChange]);

    // Delete selected rows
    const handleDeleteRows = useCallback(() => {
        if (selectedRows.size === 0) return;

        // Prevent deleting all rows
        if (selectedRows.size === data.length && data.length <= minRows) {
            alert(`Cannot delete all rows. At least ${minRows} row(s) must remain.`);
            return;
        }

        const newData = data.filter((_, index) => !selectedRows.has(index));

        // Ensure at least minRows remain
        if (newData.length < minRows) {
            alert(`Cannot delete. At least ${minRows} row(s) must remain.`);
            return;
        }

        onChange(newData);
        setSelectedRows(new Set());
    }, [data, selectedRows, minRows, onChange]);

    // Update a cell value
    const handleCellChange = useCallback((rowIndex: number, columnName: string, value: string | number) => {
        const newData = [...data];
        newData[rowIndex] = { ...newData[rowIndex], [columnName]: value };
        onChange(newData);
    }, [data, onChange]);

    // Toggle row selection
    const handleRowSelect = useCallback((rowIndex: number) => {
        const newSelected = new Set(selectedRows);
        if (newSelected.has(rowIndex)) {
            newSelected.delete(rowIndex);
        } else {
            newSelected.add(rowIndex);
        }
        setSelectedRows(newSelected);
    }, [selectedRows]);

    // Render input based on column type
    const renderCell = (row: CorrectionRow, col: ColumnDef, rowIndex: number) => {
        const value = row[col.name] ?? '';

        switch (col.type) {
            case 'datetime':
                return (
                    <input
                        type="datetime-local"
                        value={value as string}
                        onChange={(e) => handleCellChange(rowIndex, col.name, e.target.value)}
                        placeholder={col.placeholder}
                        className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                    />
                );
            case 'number':
                return (
                    <input
                        type="number"
                        step="any"
                        value={value as number}
                        onChange={(e) => handleCellChange(rowIndex, col.name, parseFloat(e.target.value) || 0)}
                        placeholder={col.placeholder}
                        className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                    />
                );
            case 'text':
                return (
                    <input
                        type="text"
                        value={value as string}
                        onChange={(e) => handleCellChange(rowIndex, col.name, e.target.value)}
                        placeholder={col.placeholder}
                        className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:ring-1 focus:ring-blue-500 focus:border-blue-500"
                    />
                );
            default:
                return null;
        }
    };

    return (
        <div className="space-y-3">
            {/* Toolbar */}
            <div className="flex justify-between items-center">
                <button
                    onClick={handleAddRow}
                    className="flex items-center gap-2 px-3 py-1.5 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                    <Plus size={16} />
                    Add Row
                </button>

                {selectedRows.size > 0 && (
                    <button
                        onClick={handleDeleteRows}
                        className="flex items-center gap-2 px-3 py-1.5 text-sm bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
                    >
                        <Trash2 size={16} />
                        Delete ({selectedRows.size})
                    </button>
                )}
            </div>

            {/* Table */}
            <div className="border border-gray-200 rounded-lg overflow-hidden">
                <div className="overflow-x-auto">
                    <table className="w-full">
                        <thead className="bg-gray-50 border-b border-gray-200">
                            <tr>
                                <th className="w-10 px-3 py-2">
                                    {/* Select column */}
                                </th>
                                {columns.map((col) => (
                                    <th key={col.name} className="px-3 py-2 text-left text-xs font-medium text-gray-700 uppercase tracking-wider">
                                        {col.label}
                                        {col.required && <span className="text-red-500 ml-1">*</span>}
                                    </th>
                                ))}
                            </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                            {data.length === 0 ? (
                                <tr>
                                    <td colSpan={columns.length + 1} className="px-3 py-8 text-center text-gray-400 text-sm">
                                        No data. Click "Add Row" to get started.
                                    </td>
                                </tr>
                            ) : (
                                data.map((row, rowIndex) => (
                                    <tr
                                        key={rowIndex}
                                        className={selectedRows.has(rowIndex) ? 'bg-blue-50' : 'hover:bg-gray-50'}
                                    >
                                        <td className="px-3 py-2">
                                            <input
                                                type="checkbox"
                                                checked={selectedRows.has(rowIndex)}
                                                onChange={() => handleRowSelect(rowIndex)}
                                                className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                                            />
                                        </td>
                                        {columns.map((col) => (
                                            <td key={col.name} className="px-3 py-2">
                                                {renderCell(row, col, rowIndex)}
                                            </td>
                                        ))}
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Helper text */}
            <p className="text-xs text-gray-500">
                Select rows using checkboxes, then click "Delete" to remove them. Press "Add Row" to add new entries.
            </p>
        </div>
    );
};

export default CorrectionTable;
export { type ColumnDef, type CorrectionRow };
