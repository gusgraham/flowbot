import React, { useState, useEffect, useCallback } from 'react';
import { Save } from 'lucide-react';
import CorrectionTable from '../../components/CorrectionTable';
import type { ColumnDef, CorrectionRow } from '../../components/CorrectionTable';

interface PumpLoggerCalibrationProps {
    installId: number;
    settings: any;
    onSave: (data: any) => void;
    isSaving: boolean;
}

const PumpLoggerCalibration: React.FC<PumpLoggerCalibrationProps> = ({
    installId,
    settings,
    onSave,
    isSaving
}) => {
    const [timingCorrections, setTimingCorrections] = useState<CorrectionRow[]>([]);
    const [addedOnOffs, setAddedOnOffs] = useState<CorrectionRow[]>([]);

    // Load settings
    useEffect(() => {
        if (settings) {
            // Parse timing corrections from JSON
            if (settings.pl_timing_corr) {
                try {
                    const parsed = JSON.parse(settings.pl_timing_corr);
                    setTimingCorrections(parsed);
                } catch (e) {
                    setTimingCorrections([]);
                }
            }

            // Parse added on/offs from JSON
            if (settings.pl_added_onoffs) {
                try {
                    const parsed = JSON.parse(settings.pl_added_onoffs);
                    setAddedOnOffs(parsed);
                } catch (e) {
                    setAddedOnOffs([]);
                }
            }
        }
    }, [settings]);

    // Column definitions
    const timingColumns: ColumnDef[] = [
        { name: 'datetime', type: 'datetime', label: 'Date/Time', required: true },
        { name: 'offset', type: 'number', label: 'Time Offset (minutes)', placeholder: '0' },
        { name: 'comment', type: 'text', label: 'Comment', placeholder: 'Optional note' },
    ];

    const onOffColumns: ColumnDef[] = [
        { name: 'datetime', type: 'datetime', label: 'Date/Time', required: true },
        { name: 'state', type: 'text', label: 'State (ON/OFF)', placeholder: 'ON or OFF' },
        { name: 'comment', type: 'text', label: 'Comment', placeholder: 'Optional note' },
    ];

    const handleSave = useCallback(() => {
        onSave({
            pl_timing_corr: JSON.stringify(timingCorrections),
            pl_added_onoffs: JSON.stringify(addedOnOffs),
        });
    }, [timingCorrections, addedOnOffs, onSave]);

    return (
        <div className="space-y-6">
            {/* Timing Corrections Table */}
            <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-3">Timing Corrections</h3>
                <p className="text-sm text-gray-600 mb-4">
                    Record any time adjustments needed for the pump logger data.
                </p>

                <CorrectionTable
                    columns={timingColumns}
                    data={timingCorrections}
                    onChange={setTimingCorrections}
                    minRows={0}
                />
            </div>

            {/* Added On/Offs Table */}
            <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-3">Added On/Off Events</h3>
                <p className="text-sm text-gray-600 mb-4">
                    Manually add pump on/off events that were not captured by the logger.
                </p>

                <CorrectionTable
                    columns={onOffColumns}
                    data={addedOnOffs}
                    onChange={setAddedOnOffs}
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

export default PumpLoggerCalibration;
