import React, { useState, useEffect } from 'react';
import { Save, Info } from 'lucide-react';
import { useUpdateAnalysisDataset } from '../../api/hooks';

interface DataEditorProps {
    datasetId: number;
    currentMetadata: Record<string, any>;
}

const DataEditor: React.FC<DataEditorProps> = ({ datasetId, currentMetadata }) => {
    const updateDataset = useUpdateAnalysisDataset();

    const [formData, setFormData] = useState({
        pipe_shape: '',
        pipe_height: '',
        pipe_width: '',
        roughness: '',
        us_invert: '',
        ds_invert: '',
        pipe_length: ''
    });

    useEffect(() => {
        // Load existing metadata into form
        setFormData({
            pipe_shape: currentMetadata?.pipe_shape || 'CIRC',
            pipe_height: currentMetadata?.pipe_height || '',
            pipe_width: currentMetadata?.pipe_width || '',
            roughness: currentMetadata?.roughness || '',
            us_invert: currentMetadata?.us_invert || '',
            ds_invert: currentMetadata?.ds_invert || '',
            pipe_length: currentMetadata?.pipe_length || ''
        });
    }, [currentMetadata]);

    const handleChange = (field: string, value: string) => {
        setFormData(prev => ({ ...prev, [field]: value }));
    };

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();

        // Convert string values to numbers where appropriate
        const updates: Record<string, any> = {
            pipe_shape: formData.pipe_shape
        };

        if (formData.pipe_height) updates.pipe_height = parseFloat(formData.pipe_height);
        if (formData.pipe_width) updates.pipe_width = parseFloat(formData.pipe_width);
        if (formData.roughness) updates.roughness = parseFloat(formData.roughness);
        if (formData.us_invert) updates.us_invert = parseFloat(formData.us_invert);
        if (formData.ds_invert) updates.ds_invert = parseFloat(formData.ds_invert);
        if (formData.pipe_length) updates.pipe_length = parseFloat(formData.pipe_length);

        // Also calculate and store diameter for circular pipes
        if (formData.pipe_shape === 'CIRC' && formData.pipe_height) {
            updates.pipe_diameter = parseFloat(formData.pipe_height);
        }

        updateDataset.mutate({ datasetId, updates });
    };

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold text-gray-900">Dataset Metadata</h3>
                {updateDataset.isSuccess && (
                    <div className="text-sm text-green-600 flex items-center gap-1">
                        <Info size={16} />
                        <span>Saved successfully</span>
                    </div>
                )}
            </div>

            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 text-sm text-blue-800">
                <p className="font-semibold mb-1">About this tab</p>
                <p>
                    Use this form to associate pipe data with this dataset. These parameters will be used to calculate
                    the Colebrook-White curve in the Scatter Graph.
                </p>
            </div>

            <form onSubmit={handleSubmit} className="bg-white border border-gray-200 rounded-lg p-6 space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {/* Pipe Shape */}
                    <div>
                        <label htmlFor="pipe_shape" className="block text-sm font-medium text-gray-700 mb-2">
                            Pipe Shape
                        </label>
                        <select
                            id="pipe_shape"
                            value={formData.pipe_shape}
                            onChange={(e) => handleChange('pipe_shape', e.target.value)}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                        >
                            <option value="CIRC">Circular</option>
                            <option value="EGG">Egg</option>
                            <option value="RECT">Rectangular</option>
                            <option value="OTHER">Other</option>
                        </select>
                    </div>

                    {/* Pipe Height */}
                    <div>
                        <label htmlFor="pipe_height" className="block text-sm font-medium text-gray-700 mb-2">
                            Pipe Height (mm)
                        </label>
                        <input
                            type="number"
                            id="pipe_height"
                            step="0.1"
                            value={formData.pipe_height}
                            onChange={(e) => handleChange('pipe_height', e.target.value)}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                            placeholder="e.g., 300"
                        />
                        {formData.pipe_shape === 'CIRC' && (
                            <p className="text-xs text-gray-500 mt-1">For circular pipes, this is the diameter</p>
                        )}
                    </div>

                    {/* Pipe Width */}
                    <div>
                        <label htmlFor="pipe_width" className="block text-sm font-medium text-gray-700 mb-2">
                            Pipe Width (mm)
                        </label>
                        <input
                            type="number"
                            id="pipe_width"
                            step="0.1"
                            value={formData.pipe_width}
                            onChange={(e) => handleChange('pipe_width', e.target.value)}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                            placeholder="e.g., 300"
                        />
                        {formData.pipe_shape === 'CIRC' && (
                            <p className="text-xs text-gray-500 mt-1">Not applicable for circular pipes</p>
                        )}
                    </div>

                    {/* Roughness */}
                    <div>
                        <label htmlFor="roughness" className="block text-sm font-medium text-gray-700 mb-2">
                            Roughness (mm)
                        </label>
                        <input
                            type="number"
                            id="roughness"
                            step="0.01"
                            value={formData.roughness}
                            onChange={(e) => handleChange('roughness', e.target.value)}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                            placeholder="e.g., 1.5"
                        />
                    </div>

                    {/* US Invert */}
                    <div>
                        <label htmlFor="us_invert" className="block text-sm font-medium text-gray-700 mb-2">
                            US Invert (mAD)
                        </label>
                        <input
                            type="number"
                            id="us_invert"
                            step="0.001"
                            value={formData.us_invert}
                            onChange={(e) => handleChange('us_invert', e.target.value)}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                            placeholder="e.g., 100.5"
                        />
                    </div>

                    {/* DS Invert */}
                    <div>
                        <label htmlFor="ds_invert" className="block text-sm font-medium text-gray-700 mb-2">
                            DS Invert (mAD)
                        </label>
                        <input
                            type="number"
                            id="ds_invert"
                            step="0.001"
                            value={formData.ds_invert}
                            onChange={(e) => handleChange('ds_invert', e.target.value)}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                            placeholder="e.g., 99.5"
                        />
                    </div>

                    {/* Pipe Length */}
                    <div>
                        <label htmlFor="pipe_length" className="block text-sm font-medium text-gray-700 mb-2">
                            Pipe Length (m)
                        </label>
                        <input
                            type="number"
                            id="pipe_length"
                            step="0.1"
                            value={formData.pipe_length}
                            onChange={(e) => handleChange('pipe_length', e.target.value)}
                            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                            placeholder="e.g., 100"
                        />
                    </div>
                </div>

                {/* Calculated Gradient Display */}
                {formData.us_invert && formData.ds_invert && formData.pipe_length && (
                    <div className="bg-gray-50 p-4 rounded-md">
                        <p className="text-sm font-medium text-gray-700 mb-2">Calculated Gradient</p>
                        <p className="text-lg font-semibold text-purple-600">
                            {((parseFloat(formData.us_invert) - parseFloat(formData.ds_invert)) / parseFloat(formData.pipe_length) * 100).toFixed(3)}%
                        </p>
                        <p className="text-xs text-gray-500 mt-1">
                            Based on: (US Invert - DS Invert) / Pipe Length
                        </p>
                    </div>
                )}

                <div className="flex justify-end gap-3 pt-4 border-t border-gray-200">
                    <button
                        type="submit"
                        disabled={updateDataset.isPending}
                        className="bg-purple-600 text-white px-6 py-2 rounded-lg hover:bg-purple-700 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed flex items-center gap-2"
                    >
                        <Save size={18} />
                        {updateDataset.isPending ? 'Saving...' : 'Save Changes'}
                    </button>
                </div>

                {updateDataset.isError && (
                    <div className="bg-red-50 border border-red-200 text-red-600 p-3 rounded-md text-sm">
                        Error saving changes. Please try again.
                    </div>
                )}
            </form>
        </div>
    );
};

export default DataEditor;
