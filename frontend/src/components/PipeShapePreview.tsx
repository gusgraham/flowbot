import React, { useMemo } from 'react';

interface PipeShapePreviewProps {
    shape: string;
    width: number;
    height: number;
    intervals: number;
}

interface Point {
    w: number;
    h: number;
}

const PipeShapePreview: React.FC<PipeShapePreviewProps> = ({ shape, width, height, intervals }) => {

    // Generate shape points using the legacy algorithm
    const points = useMemo(() => {
        if (!width || !height) return [];

        try {
            return generateShape(width, height, intervals, shape);
        } catch (error) {
            console.error('Shape generation error:', error);
            return [];
        }
    }, [width, height, intervals, shape]);

    // Generate smooth background shape with many intervals for comparison
    const smoothPoints = useMemo(() => {
        if (!width || !height) return [];

        try {
            return generateShape(width, height, 100, shape); // Always use 100 intervals for smooth background
        } catch (error) {
            return [];
        }
    }, [width, height, shape]);

    const viewBoxSize = 400;
    const padding = 40;
    const maxDim = Math.max(width, height);
    const scale = (viewBoxSize - 2 * padding) / maxDim;

    const centerX = viewBoxSize / 2;
    const baseY = viewBoxSize - padding;

    // Convert points to SVG path
    const pathData = useMemo(() => {
        if (points.length === 0) return '';

        const leftPoints = points.map(p => ({
            x: centerX - (p.w / 2) * scale,
            y: baseY - p.h * scale
        }));

        const rightPoints = points.map(p => ({
            x: centerX + (p.w / 2) * scale,
            y: baseY - p.h * scale
        })).reverse();

        const allPoints = [...leftPoints, ...rightPoints];

        const path = allPoints.map((p, i) =>
            `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`
        ).join(' ') + ' Z';

        return path;
    }, [points, scale, centerX, baseY]);

    // Convert smooth points to SVG path for background
    const smoothPathData = useMemo(() => {
        if (smoothPoints.length === 0) return '';

        const leftPoints = smoothPoints.map(p => ({
            x: centerX - (p.w / 2) * scale,
            y: baseY - p.h * scale
        }));

        const rightPoints = smoothPoints.map(p => ({
            x: centerX + (p.w / 2) * scale,
            y: baseY - p.h * scale
        })).reverse();

        const allPoints = [...leftPoints, ...rightPoints];

        const path = allPoints.map((p, i) =>
            `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`
        ).join(' ') + ' Z';

        return path;
    }, [smoothPoints, scale, centerX, baseY]);

    const errorMessage = useMemo(() => {
        const shapeUpper = shape.toUpperCase();

        if (shapeUpper === 'ARCH' && height <= width / 2) {
            return 'ARCH requires H > W/2';
        }
        if (shapeUpper === 'CIRC' && height !== width) {
            return 'CIRC requires H = W';
        }
        if (shapeUpper === 'CNET' && !(width / 2 < height && height < width)) {
            return 'CNET requires W/2 < H < W';
        }
        if (shapeUpper === 'EGG' && !(width < height && height < 2 * width)) {
            return 'EGG requires W < H < 2W';
        }
        if (shapeUpper === 'EGG2' && !(width < height && height < 3 * width)) {
            return 'EGG2 requires W < H < 3W';
        }
        if (shapeUpper === 'OVAL' && height <= width) {
            return 'OVAL requires H > W';
        }
        if (shapeUpper === 'UTOP' && height <= width / 2) {
            return 'UTOP requires H > W/2';
        }

        return null;
    }, [shape, width, height]);

    return (
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
            <div className="flex justify-between items-center mb-3">
                <h4 className="text-sm font-medium text-gray-700">Shape Preview</h4>
                <span className="text-xs text-gray-500">{intervals} intervals</span>
            </div>

            {errorMessage ? (
                <div className="w-full h-64 bg-white rounded border border-red-300 flex items-center justify-center">
                    <div className="text-center">
                        <p className="text-red-600 font-medium mb-1">Invalid Dimensions</p>
                        <p className="text-sm text-red-500">{errorMessage}</p>
                    </div>
                </div>
            ) : shape === 'USER' ? (
                <div className="w-full h-64 bg-white rounded border border-gray-200 flex items-center justify-center">
                    <p className="text-gray-500 text-sm">Define shape using table below</p>
                </div>
            ) : (
                <svg
                    viewBox={`0 0 ${viewBoxSize} ${viewBoxSize}`}
                    className="w-full h-64 bg-white rounded border border-gray-200"
                >
                    {/* Grid lines */}
                    <line x1={padding} y1={baseY} x2={viewBoxSize - padding} y2={baseY} stroke="#E5E7EB" strokeWidth="1" />
                    <line x1={centerX} y1={padding} x2={centerX} y2={viewBoxSize - padding} stroke="#E5E7EB" strokeWidth="1" />

                    {/* Smooth background shape (true shape) */}
                    {smoothPathData && (
                        <path
                            d={smoothPathData}
                            fill="none"
                            stroke="#9CA3AF"
                            strokeWidth="2.5"
                        />
                    )}

                    {/* User's interval-based shape */}
                    {pathData && (
                        <>
                            <path
                                d={pathData}
                                fill="rgba(59, 130, 246, 0.1)"
                                stroke="#3B82F6"
                                strokeWidth="2"
                            />

                            {/* Show discrete points to visualize intervals */}
                            {points.map((p, i) => {
                                const leftX = centerX - (p.w / 2) * scale;
                                const rightX = centerX + (p.w / 2) * scale;
                                const y = baseY - p.h * scale;

                                return (
                                    <g key={i}>
                                        <circle cx={leftX} cy={y} r="2" fill="#EF4444" />
                                        <circle cx={rightX} cy={y} r="2" fill="#EF4444" />
                                    </g>
                                );
                            })}
                        </>
                    )}

                    {/* Dimension labels */}
                    <text x={centerX} y={baseY + 25} textAnchor="middle" fill="#374151" fontSize="14" fontWeight="600">
                        {width}mm
                    </text>
                    <text
                        x={centerX - (width * scale / 2) - 25}
                        y={baseY - (height * scale / 2)}
                        textAnchor="middle"
                        fill="#374151"
                        fontSize="14"
                        fontWeight="600"
                        transform={`rotate(-90 ${centerX - (width * scale / 2) - 25} ${baseY - (height * scale / 2)})`}
                    >
                        {height}mm
                    </text>
                </svg>
            )}
        </div>
    );
};

// Port of the legacy generate_shape function
function generateShape(width: number, height: number, intervals: number, shapeType: string): Point[] {
    if (intervals < 2) {
        throw new Error("Number of intervals must be at least 2.");
    }

    const heights = Array.from({ length: intervals }, (_, i) => i * height / (intervals - 1));
    const points: Point[] = [];
    const shape = shapeType.toUpperCase();

    if (shape === 'ARCH') {
        if (height <= width / 2) {
            throw new Error("ARCH requires H > W/2.");
        }
        const radius = width / 2;
        const flatHeight = height - radius;

        for (const h of heights) {
            let w: number;
            if (h >= flatHeight) {
                const offset = h - flatHeight;
                w = 2 * Math.sqrt(radius ** 2 - offset ** 2);
            } else {
                w = width;
            }
            points.push({ w, h });
        }
    } else if (shape === 'CIRC') {
        if (height !== width) {
            throw new Error("CIRC requires H = W.");
        }
        const radius = width / 2;
        const center = height / 2;

        for (const h of heights) {
            const offset = Math.abs(h - center);
            const w = offset <= radius ? 2 * Math.sqrt(radius ** 2 - offset ** 2) : 0;
            points.push({ w, h });
        }
    } else if (shape === 'CNET') {
        if (!(width / 2 < height && height < width)) {
            throw new Error("CNET requires W/2 < H < W.");
        }
        const topRadius = width / 2;
        const bottomRadius = height - topRadius;
        const topCenter = height - topRadius;
        const bottomCenter = bottomRadius;

        for (const h of heights) {
            let w: number;
            if (h >= topCenter) {
                const offset = h - topCenter;
                w = Math.abs(offset) <= topRadius ? 2 * Math.sqrt(topRadius ** 2 - offset ** 2) : 0;
            } else if (h <= bottomCenter) {
                const offset = bottomCenter - h;
                w = Math.abs(offset) <= bottomRadius ? 2 * Math.sqrt(bottomRadius ** 2 - offset ** 2) : 0;
            } else {
                w = width;
            }
            points.push({ w, h });
        }
    } else if (shape === 'EGG') {
        if (!(width < height && height < 2 * width)) {
            throw new Error("EGG requires W < H < 2W.");
        }
        const topRadius = width / 2;
        const bottomRadius = (height - width) / 2;
        const topCenter = height - topRadius;
        const bottomCenter = bottomRadius;

        for (const h of heights) {
            let w: number;
            if (h >= topCenter) {
                const offset = h - topCenter;
                w = 2 * Math.sqrt(topRadius ** 2 - offset ** 2);
            } else if (h <= bottomCenter) {
                const offset = bottomCenter - h;
                w = 2 * Math.sqrt(bottomRadius ** 2 - offset ** 2);
            } else {
                w = (height - width) + ((width - (height - width)) * (h - bottomCenter) / (topCenter - bottomCenter));
            }
            points.push({ w, h });
        }
    } else if (shape === 'EGG2') {
        if (!(width < height && height < 3 * width)) {
            throw new Error("EGG2 requires W < H < 3W.");
        }
        const topRadius = width / 2;
        const gapHeight = 0.5 * (height - width);
        const bottomRadius = gapHeight / 2;
        const topCenter = height - topRadius;
        const bottomCenter = bottomRadius;

        for (const h of heights) {
            let w: number;
            if (h >= topCenter) {
                const offset = h - topCenter;
                w = offset <= topRadius ? 2 * Math.sqrt(topRadius ** 2 - offset ** 2) : 0;
            } else if (h >= bottomCenter) {
                const bottomDiameter = 2 * bottomRadius;
                w = bottomDiameter + ((width - bottomDiameter) * (h - bottomCenter) / (topCenter - bottomCenter));
            } else {
                const offset = h - bottomCenter;
                w = offset <= bottomRadius ? 2 * Math.sqrt(bottomRadius ** 2 - offset ** 2) : 0;
            }
            points.push({ w, h });
        }
    } else if (shape === 'OVAL') {
        if (height <= width) {
            throw new Error("OVAL requires H > W.");
        }
        const radius = width / 2;
        const topCenter = height - radius;
        const bottomCenter = radius;

        for (const h of heights) {
            let w: number;
            if (h >= topCenter) {
                const offset = h - topCenter;
                w = Math.abs(offset) <= radius ? 2 * Math.sqrt(radius ** 2 - offset ** 2) : 0;
            } else if (h <= bottomCenter) {
                const offset = bottomCenter - h;
                w = Math.abs(offset) <= radius ? 2 * Math.sqrt(radius ** 2 - offset ** 2) : 0;
            } else {
                w = width;
            }
            points.push({ w, h });
        }
    } else if (shape === 'RECT') {
        for (const h of heights) {
            points.push({ w: width, h });
        }
    } else if (shape === 'UTOP') {
        if (height <= width / 2) {
            throw new Error("UTOP requires H > W/2.");
        }
        const radius = width / 2;
        const flatHeightStart = radius;

        for (const h of heights) {
            let w: number;
            if (h <= flatHeightStart) {
                const offset = Math.abs(h - flatHeightStart);
                w = offset <= radius ? 2 * Math.sqrt(radius ** 2 - offset ** 2) : 0;
            } else {
                w = width;
            }
            points.push({ w, h });
        }
    } else {
        throw new Error(`Unsupported shape: ${shapeType}`);
    }

    return points;
}

export default PipeShapePreview;
