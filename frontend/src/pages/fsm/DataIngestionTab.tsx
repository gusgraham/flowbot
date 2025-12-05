import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { Folder, Info, Save, Check, X, AlertCircle } from 'lucide-react';
import { useRawDataSettings, useUpdateRawDataSettings, useInstall } from '../../api/hooks';
import api from '../../api/client';

interface DataIngestionTabProps {
    installId: number;
    installType: string;
}

// Template tokens - defined outside component to prevent recreation
const TOKENS = [
    { id: 'pmac_id', label: 'PMAC ID', token: '{pmac_id}' },
    { id: 'ast_id', label: 'Asset ID', token: '{ast_id}' },
    { id: 'inst_id', label: 'Install ID', token: '{inst_id}' },
    { id: 'cl_ref', label: 'Client Ref', token: '{cl_ref}' },
    { id: 'site_id', label: 'Site ID', token: '{site_id}' },
    { id: 'prj_id', label: 'Project ID', token: '{prj_id}' },
];

// FileFormatInput component - defined outside to prevent recreation
interface FileFormatInputProps {
    label: string;
    value: string;
    onChange: (val: string) => void;
    placeholder: string;
    onTokenInsert: (token: string) => void;
    folderPath: string;
    installId: number;
}

const FileFormatInput: React.FC<FileFormatInputProps> = React.memo(({
    label,
    value,
    onChange,
    placeholder,
    onTokenInsert,
    folderPath,
    installId
}) => {
    const [resolvedFilename, setResolvedFilename] = useState<string>('');
    const [fileExists, setFileExists] = useState<boolean | null>(null);
    const [isValidating, setIsValidating] = useState(false);

    // Fetch resolved filename and validate when value or folder changes
    useEffect(() => {
        if (!value || !folderPath) {
            setResolvedFilename('');
            setFileExists(null);
            return;
        }

        const validateFile = async () => {
            setIsValidating(true);
            try {
                const { data } = await api.post(`/installs/${installId}/validate-file`, null, {
                    params: {
                        file_path: folderPath,
                        file_format: value
                    }
                });
                setResolvedFilename(data.resolved_path);
                setFileExists(data.exists);
            } catch (error) {
                setResolvedFilename('Error resolving');
                setFileExists(false);
            } finally {
                setIsValidating(false);
            }
        };

        const debounce = setTimeout(validateFile, 500);
        return () => clearTimeout(debounce);
    }, [value, folderPath, installId]);

    return (
        <div className="space-y-2">
            <label className="block text-sm font-medium text-gray-700">{label}</label>

            {/* Input and Preview side by side */}
            <div className="grid grid-cols-2 gap-3">
                {/* Input */}
                <div>
                    <input
                        type="text"
                        value={value}
                        onChange={(e) => onChange(e.target.value)}
                        placeholder={placeholder}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    />
                </div>

                {/* Preview */}
                <div className={`
                    flex items-center gap-2 px-3 py-2 rounded-lg border
                    ${!value ? 'bg-gray-50 border-gray-200' :
                        fileExists === true ? 'bg-green-50 border-green-300' :
                            fileExists === false ? 'bg-red-50 border-red-300' :
                                'bg-gray-50 border-gray-300'}
                `}>
                    {isValidating ? (
                        <span className="text-xs text-gray-500">Validating...</span>
                    ) : !value ? (
                        <span className="text-xs text-gray-400 italic">No format specified</span>
                    ) : !folderPath ? (
                        <div className="flex items-center gap-1">
                            <AlertCircle size={14} className="text-amber-500" />
                            <span className="text-xs text-amber-700">Set folder path first</span>
                        </div>
                    ) : (
                        <>
                            {fileExists !== null && (
                                <div className="flex-shrink-0">
                                    {fileExists ? (
                                        <Check size={16} className="text-green-600" />
                                    ) : (
                                        <X size={16} className="text-red-600" />
                                    )}
                                </div>
                            )}
                            <code className="text-xs text-gray-700 font-mono truncate" title={resolvedFilename}>
                                {resolvedFilename}
                            </code>
                        </>
                    )}
                </div>
            </div>

            {/* Token buttons */}
            <div className="flex flex-wrap gap-2">
                {TOKENS.map((token) => (
                    <button
                        key={token.id}
                        onClick={() => onTokenInsert(token.token)}
                        type="button"
                        className="px-2 py-1 text-xs bg-blue-100 text-blue-700 rounded hover:bg-blue-200 transition-colors"
                        title={`Insert ${token.label}`}
                    >
                        {token.label}
                    </button>
                ))}
            </div>
        </div>
    );
});

FileFormatInput.displayName = 'FileFormatInput';

const DataIngestionTab: React.FC<DataIngestionTabProps> = ({ installId, installType }) => {
    const { data: settings, isLoading } = useRawDataSettings(installId);
    const { mutate: updateSettings, isPending } = useUpdateRawDataSettings();

    const [folderPath, setFolderPath] = useState('');
    const [rainfallFormat, setRainfallFormat] = useState('');
    const [depthFormat, setDepthFormat] = useState('');
    const [velocityFormat, setVelocityFormat] = useState('');
    const [batteryFormat, setBatteryFormat] = useState('');
    const [pumpLoggerFormat, setPumpLoggerFormat] = useState('');

    // Load settings when data is fetched
    useEffect(() => {
        if (settings) {
            setFolderPath(settings.file_path || '');
            setRainfallFormat(settings.rainfall_file_format || '');
            setDepthFormat(settings.depth_file_format || '');
            setVelocityFormat(settings.velocity_file_format || '');
            setBatteryFormat(settings.battery_file_format || '');
            setPumpLoggerFormat(settings.pumplogger_file_format || '');
        }
    }, [settings]);

    // Stable token insert handlers
    const handleRainfallTokenInsert = useCallback((token: string) => {
        setRainfallFormat(prev => prev + token);
    }, []);

    const handleDepthTokenInsert = useCallback((token: string) => {
        setDepthFormat(prev => prev + token);
    }, []);

    const handleVelocityTokenInsert = useCallback((token: string) => {
        setVelocityFormat(prev => prev + token);
    }, []);

    const handleBatteryTokenInsert = useCallback((token: string) => {
        setBatteryFormat(prev => prev + token);
    }, []);

    const handlePumpLoggerTokenInsert = useCallback((token: string) => {
        setPumpLoggerFormat(prev => prev + token);
    }, []);

    const handleSave = useCallback(() => {
        updateSettings({
            installId,
            settings: {
                file_path: folderPath,
                rainfall_file_format: rainfallFormat,
                depth_file_format: depthFormat,
                velocity_file_format: velocityFormat,
                battery_file_format: batteryFormat,
                pumplogger_file_format: pumpLoggerFormat,
            },
        });
    }, [installId, folderPath, rainfallFormat, depthFormat, velocityFormat, batteryFormat, pumpLoggerFormat, updateSettings]);

    if (isLoading) {
        return <div className="text-center py-8 text-gray-400">Loading settings...</div>;
    }

    return (
        <div className="space-y-6">
            {/* Folder Path */}
            <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                    <Folder size={16} className="inline mr-1" />
                    Data Folder Path
                </label>
                <input
                    type="text"
                    value={folderPath}
                    onChange={(e) => setFolderPath(e.target.value)}
                    placeholder="C:\Data\Project"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
                <p className="text-xs text-gray-500 mt-1">
                    Base folder where raw data files are stored
                </p>
            </div>

            {/* Info Box */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div className="flex gap-2">
                    <Info className="text-blue-600 flex-shrink-0" size={20} />
                    <div className="text-sm text-blue-900">
                        <p className="font-medium mb-1">File Format Templates</p>
                        <p>Click the token buttons to insert placeholders. The preview on the right shows the resolved filename and validates if the file exists (✓ = found, ✗ = not found).</p>
                    </div>
                </div>
            </div>

            {/* File Format Inputs - Install Type Specific */}
            {installType === 'Rain Gauge' && (
                <FileFormatInput
                    label="Rainfall File Format"
                    value={rainfallFormat}
                    onChange={setRainfallFormat}
                    placeholder="rainfall_{inst_id}.csv"
                    onTokenInsert={handleRainfallTokenInsert}
                    folderPath={folderPath}
                    installId={installId}
                />
            )}

            {(installType === 'Flow Monitor' || installType === 'Depth Monitor') && (
                <>
                    <FileFormatInput
                        label="Depth File Format"
                        value={depthFormat}
                        onChange={setDepthFormat}
                        placeholder="depth_{pmac_id}.csv"
                        onTokenInsert={handleDepthTokenInsert}
                        folderPath={folderPath}
                        installId={installId}
                    />

                    <FileFormatInput
                        label="Velocity File Format"
                        value={velocityFormat}
                        onChange={setVelocityFormat}
                        placeholder="velocity_{pmac_id}.csv"
                        onTokenInsert={handleVelocityTokenInsert}
                        folderPath={folderPath}
                        installId={installId}
                    />

                    <FileFormatInput
                        label="Battery File Format"
                        value={batteryFormat}
                        onChange={setBatteryFormat}
                        placeholder="battery_{pmac_id}.csv"
                        onTokenInsert={handleBatteryTokenInsert}
                        folderPath={folderPath}
                        installId={installId}
                    />
                </>
            )}

            {installType === 'Pump Logger' && (
                <FileFormatInput
                    label="Pump Logger File Format"
                    value={pumpLoggerFormat}
                    onChange={setPumpLoggerFormat}
                    placeholder="pumplogger_{inst_id}.csv"
                    onTokenInsert={handlePumpLoggerTokenInsert}
                    folderPath={folderPath}
                    installId={installId}
                />
            )}

            {/* Save Button */}
            <div className="flex justify-end gap-3 pt-4 border-t">
                <button
                    onClick={handleSave}
                    disabled={isPending}
                    className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                    <Save size={18} />
                    {isPending ? 'Saving...' : 'Save Settings'}
                </button>
            </div>
        </div>
    );
};

export default DataIngestionTab;
