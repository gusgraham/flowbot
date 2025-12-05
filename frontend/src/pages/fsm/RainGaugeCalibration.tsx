import React, { useState, useEffect, useCallback } from 'react';
import { Save } from 'lucide-react';
import CorrectionTable from '../../components/CorrectionTable';
import type { ColumnDef, CorrectionRow } from '../../components/CorrectionTable';

interface RainGaugeCalibrationProps {
    installId: number;
    settings: any;
    onSave: (data: any) => void;
    isSaving: boolean;
}

const RainGaugeCalibration: React.FC<RainGaugeCalibrationProps> = ({
    installId,
    settings,
    onSave,
    isSaving
}) => {
    const [tippingBucketDepth, setTippingBucketDepth] = useState<number>(0.2);
    const [timingCorrections, setTimingCorrections] = useState<CorrectionRow[]>([]);

    // Load settings
    useEffect(() => {
        if (settings) {
            setTippingBucketDepth(settings.rg_tb_depth || 0.2);

            // Parse timing corrections from JSON
            if (settings.rg_timing_corr) {
                try {
                    const parsed = JSON.parse(settings.rg_timing_corr);
                    setTimingCorrections(parsed);
                } catch (e) {
                    setTimingCorrections([]);
                }
            }
        }
    }, [settings]);

    // Column definitions for timing corrections table
    const timingColumns: ColumnDef[] = [
        { name: 'datetime', type: 'datetime', label: 'Date/Time', required: true },
        { name: 'offset', type: 'number', label: 'Time Offset (minutes)', placeholder: '0' },
        { name: 'comment', type: 'text', label: 'Comment', placeholder: 'Optional note' },
    ];

    const handleSave = useCallback(() => {
        onSave({
            rg_tb_depth: tippingBucketDepth,
            rg_timing_corr: JSON.stringify(timingCorrections),
        });
    }, [tippingBucketDepth, timingCorrections, onSave]);

    return (
        <div className="space-y-6">
            {/* Tipping Bucket Depth */}
            <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                    Tipping Bucket Depth (mm)
                </label>
                <input
                    type="number"
                    step="0.01"
                    value={tippingBucketDepth}
                    onChange={(e) => setTippingBucketDepth(parseFloat(e.target.value) || 0)}
                    className="w-64 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
                <p className="text-xs text-gray-500 mt-1">
                    Depth of rainfall per tip (typically 0.2mm or 0.5mm)
                </p>
            </div>

            {/* Timing Corrections Table */}
            <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-3">Timing Corrections</h3>
                <p className="text-sm text-gray-600 mb-4">
                    Record any time adjustments needed for the rainfall data logger.
                </p>

                <CorrectionTable
                    columns={timingColumns}
                    data={timingCorrections}
                    onChange={setTimingCorrections}
                    minRows={0}
                />
            </div>

            {/* Save Button */}
            <div className="flex justify-end gap-3 pt-4 border-t">
                <button
                    onClick={handleSave}
                    disabled={isSaving}
                    className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                    <Save size={18} />
                    {isSaving ? 'Saving...' : 'Save Calibration'}
                </button>
            </div>
        </div>
    );
};

export default RainGaugeCalibration;
