import React, { useState, useEffect, useCallback } from 'react';
import { Save } from 'lucide-react';
import CorrectionTable from '../../components/CorrectionTable';
import PipeShapePreview from '../../components/PipeShapePreview';
import type { ColumnDef, CorrectionRow } from '../../components/CorrectionTable';
import { useToast } from '../../contexts/ToastContext';

interface FlowMonitorCalibrationProps {
    installId: number;
    settings: any;
    onSave: (data: any) => void;
    isSaving: boolean;
}

const PIPE_SHAPES = [
    { value: 'ARCH', label: 'ARCH' },
    { value: 'CIRC', label: 'CIRC' },
    { value: 'CNET', label: 'CNET' },
    { value: 'EGG', label: 'EGG' },
    { value: 'EGG2', label: 'EGG2' },
    { value: 'OVAL', label: 'OVAL' },
    { value: 'RECT', label: 'RECT' },
    { value: 'UTOP', label: 'UTOP' },
    { value: 'USER', label: 'USER' },
];

const FlowMonitorCalibration: React.FC<FlowMonitorCalibrationProps> = ({
    installId,
    settings,
    onSave,
    isSaving
}) => {
    const [pipeShape, setPipeShape] = useState<string>('CIRC');
    const [pipeWidth, setPipeWidth] = useState<number>(300);
    const [pipeHeight, setPipeHeight] = useState<number>(300);
    const [pipeShapeIntervals, setPipeShapeIntervals] = useState<number>(20);
    const [pipeShapeDef, setPipeShapeDef] = useState<CorrectionRow[]>([]);

    const [depthCorrections, setDepthCorrections] = useState<CorrectionRow[]>([]);
    const [velocityCorrections, setVelocityCorrections] = useState<CorrectionRow[]>([]);
    const [timingCorrections, setTimingCorrections] = useState<CorrectionRow[]>([]);
    const [siltLevels, setSiltLevels] = useState<CorrectionRow[]>([]);

    // Load settings
    useEffect(() => {
        if (settings) {
            setPipeShape(settings.pipe_shape || 'CIRC');
            setPipeWidth(settings.pipe_width || 300);
            setPipeHeight(settings.pipe_height || 300);
            setPipeShapeIntervals(settings.pipe_shape_intervals || 20);

            // Parse JSON fields
            if (settings.pipe_shape_def) {
                try {
                    setPipeShapeDef(JSON.parse(settings.pipe_shape_def));
                } catch (e) {
                    setPipeShapeDef([]);
                }
            }

            if (settings.dep_corr) {
                try {
                    setDepthCorrections(JSON.parse(settings.dep_corr));
                } catch (e) {
                    setDepthCorrections([]);
                }
            }

            if (settings.vel_corr) {
                try {
                    setVelocityCorrections(JSON.parse(settings.vel_corr));
                } catch (e) {
                    setVelocityCorrections([]);
                }
            }

            if (settings.dv_timing_corr) {
                try {
                    setTimingCorrections(JSON.parse(settings.dv_timing_corr));
                } catch (e) {
                    setTimingCorrections([]);
                }
            }

            if (settings.silt_levels) {
                try {
                    setSiltLevels(JSON.parse(settings.silt_levels));
                } catch (e) {
                    setSiltLevels([]);
                }
            }
        }
    }, [settings]);

    // Column definitions
    const pipeShapeColumns: ColumnDef[] = [
        { name: 'width', type: 'number', label: 'Width (mm)', required: true },
        { name: 'height', type: 'number', label: 'Height (mm)', required: true },
    ];

    const depthColumns: ColumnDef[] = [
        { name: 'datetime', type: 'datetime', label: 'Date/Time', required: true },
        { name: 'depth_corr', type: 'number', label: 'Depth Correction (mm)', placeholder: '0' },
        { name: 'invert_offset', type: 'number', label: 'Invert Offset (mm)', placeholder: '0' },
        { name: 'comment', type: 'text', label: 'Comment', placeholder: 'Optional note' },
    ];

    const velocityColumns: ColumnDef[] = [
        { name: 'datetime', type: 'datetime', label: 'Date/Time', required: true },
        { name: 'velocity_factor', type: 'number', label: 'Velocity Factor', placeholder: '1.0' },
        { name: 'comment', type: 'text', label: 'Comment', placeholder: 'Optional note' },
    ];

    const timingColumns: ColumnDef[] = [
        { name: 'datetime', type: 'datetime', label: 'Date/Time', required: true },
        { name: 'time_offset', type: 'number', label: 'Time Offset (minutes)', placeholder: '0' },
        { name: 'comment', type: 'text', label: 'Comment', placeholder: 'Optional note' },
    ];

    const siltColumns: ColumnDef[] = [
        { name: 'datetime', type: 'datetime', label: 'Date/Time', required: true },
        { name: 'silt_depth', type: 'number', label: 'Silt Depth (mm)', placeholder: '0' },
        { name: 'comment', type: 'text', label: 'Comment', placeholder: 'Optional note' },
    ];

    const { error: toastError } = useToast();

    const handleSave = useCallback(() => {
        // Validation
        if (pipeWidth <= 0 || pipeHeight <= 0) {
            toastError('Pipe width and height must be greater than 0');
            return;
        }

        if (pipeShape === 'CIRC' && pipeWidth !== pipeHeight) {
            toastError('Circular pipes must have equal width and height');
            return;
        }

        if (pipeShape === 'USER' && pipeShapeDef.length < 2) {
            toastError('User defined shapes must have at least 2 points');
            return;
        }

        // Validate table required fields
        const validateTable = (data: CorrectionRow[], name: string) => {
            for (const row of data) {
                if (!row.datetime) {
                    toastError(`Date/Time is required for all rows in ${name}`);
                    return false;
                }
            }
            return true;
        };

        if (!validateTable(depthCorrections, 'Depth Corrections')) return;
        if (!validateTable(velocityCorrections, 'Velocity Corrections')) return;
        if (!validateTable(timingCorrections, 'Timing Corrections')) return;
        if (!validateTable(siltLevels, 'Silt Levels')) return;

        onSave({
            pipe_shape: pipeShape,
            pipe_width: pipeWidth,
            pipe_height: pipeHeight,
            pipe_shape_intervals: pipeShapeIntervals,
            pipe_shape_def: JSON.stringify(pipeShapeDef),
            dep_corr: JSON.stringify(depthCorrections),
            vel_corr: JSON.stringify(velocityCorrections),
            dv_timing_corr: JSON.stringify(timingCorrections),
            silt_levels: JSON.stringify(siltLevels),
        });
    }, [pipeShape, pipeWidth, pipeHeight, pipeShapeIntervals, pipeShapeDef,
        depthCorrections, velocityCorrections, timingCorrections, siltLevels, onSave, toastError]);

    return (
        <div className="space-y-8">
            {/* Pipe Shape Section */}
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Pipe Shape Configuration</h3>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                    {/* Pipe Shape */}
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                            Pipe Shape
                        </label>
                        <select
                            value={pipeShape}
                            onChange={(e) => setPipeShape(e.target.value)}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        >
                            {PIPE_SHAPES.map(shape => (
                                <option key={shape.value} value={shape.value}>
                                    {shape.label}
                                </option>
                            ))}
                        </select>
                    </div>

                    {/* Intervals */}
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                            Shape Intervals
                        </label>
                        <input
                            type="number"
                            value={pipeShapeIntervals}
                            onChange={(e) => setPipeShapeIntervals(parseInt(e.target.value) || 20)}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        />
                        <p className="text-xs text-gray-500 mt-1">
                            Number of intervals for shape generation
                        </p>
                    </div>

                    {/* Width */}
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                            Pipe Width (mm)
                        </label>
                        <input
                            type="number"
                            value={pipeWidth}
                            onChange={(e) => setPipeWidth(parseInt(e.target.value) || 0)}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        />
                    </div>

                    {/* Height */}
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                            Pipe Height (mm)
                        </label>
                        <input
                            type="number"
                            value={pipeHeight}
                            onChange={(e) => setPipeHeight(parseInt(e.target.value) || 0)}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                        />
                    </div>
                </div>

                {/* Shape Preview */}
                <div className="mt-4">
                    <PipeShapePreview
                        shape={pipeShape}
                        width={pipeWidth}
                        height={pipeHeight}
                        intervals={pipeShapeIntervals}
                    />
                </div>

                {/* User-defined shape table */}
                {pipeShape === 'USER' && (
                    <div className="mt-4">
                        <h4 className="text-sm font-medium text-gray-700 mb-3">User-Defined Shape Points</h4>
                        <CorrectionTable
                            columns={pipeShapeColumns}
                            data={pipeShapeDef}
                            onChange={setPipeShapeDef}
                            minRows={2}
                        />
                    </div>
                )}
            </div>

            {/* Depth Corrections */}
            <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-3">Depth Corrections</h3>
                <p className="text-sm text-gray-600 mb-4">
                    Record depth sensor calibration adjustments and invert level changes.
                </p>
                <CorrectionTable
                    columns={depthColumns}
                    data={depthCorrections}
                    onChange={setDepthCorrections}
                    minRows={0}
                />
            </div>

            {/* Velocity Corrections */}
            <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-3">Velocity Corrections</h3>
                <p className="text-sm text-gray-600 mb-4">
                    Record velocity sensor calibration factors.
                </p>
                <CorrectionTable
                    columns={velocityColumns}
                    data={velocityCorrections}
                    onChange={setVelocityCorrections}
                    minRows={0}
                />
            </div>

            {/* Timing Corrections */}
            <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-3">Timing Corrections</h3>
                <p className="text-sm text-gray-600 mb-4">
                    Record time adjustments for the flow monitor logger.
                </p>
                <CorrectionTable
                    columns={timingColumns}
                    data={timingCorrections}
                    onChange={setTimingCorrections}
                    minRows={0}
                />
            </div>

            {/* Silt Levels */}
            <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-3">Silt Levels</h3>
                <p className="text-sm text-gray-600 mb-4">
                    Record observed silt accumulation depths.
                </p>
                <CorrectionTable
                    columns={siltColumns}
                    data={siltLevels}
                    onChange={setSiltLevels}
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

export default FlowMonitorCalibration;
