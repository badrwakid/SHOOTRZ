import React, { useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, LayoutChangeEvent } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { SHOOTRZ_THEME } from '../constants/theme';

interface FrameData {
  frame_number: number;
	elbow_angle: number;
	knee_angle: number;
	release_angle: number;
	body_alignment: number;
}

interface AngleGraphProps {
  frameData: FrameData[];
  onFrameSelect?: (frameNumber: number) => void;
  selectedFrame?: number;
}

export const AngleGraph: React.FC<AngleGraphProps> = ({
  frameData,
  onFrameSelect,
  selectedFrame,
}) => {
  const [selectedMetric, setSelectedMetric] = useState<'elbow' | 'knee' | 'release' | 'alignment'>(
    'elbow'
  );
  const [showAllMetrics, setShowAllMetrics] = useState(false);
  const [graphWidth, setGraphWidth] = useState<number>(0);
  const yAxisWidth = 30;

  // Determine which metrics are actually present (non-zero, finite)
  const metricPresence = {
    elbow: frameData.some((f) => Number.isFinite(f.elbow_angle)),
    knee: frameData.some((f) => Number.isFinite(f.knee_angle)),
    release: frameData.some((f) => Number.isFinite(f.release_angle)),
    alignment: frameData.some((f) => Number.isFinite(f.body_alignment) && Math.abs(f.body_alignment) > 1e-3),
  };
  const availableMetrics = (['elbow', 'knee', 'release', 'alignment'] as const).filter(
    (m) => metricPresence[m]
  );

  // Fallback selection to the first available metric
  React.useEffect(() => {
    if (!availableMetrics.includes(selectedMetric)) {
      setSelectedMetric(availableMetrics[0] ?? 'elbow');
    }
  }, [availableMetrics.join(','), selectedMetric]);

  if (!frameData || frameData.length === 0) {
    return (
      <View style={styles.emptyContainer}>
        <Ionicons name="analytics-outline" size={48} color={SHOOTRZ_THEME.colors.textSecondary} />
        <Text style={styles.emptyText}>No frame data available</Text>
      </View>
    );
  }

  const getMetricData = (metric: string) => {
		const keyMap: Record<string, keyof FrameData> = {
			elbow: 'elbow_angle',
			knee: 'knee_angle',
			release: 'release_angle',
			alignment: 'body_alignment',
		};
		const key = keyMap[metric] ?? 'elbow_angle';

		return frameData.map((frame) => {
			const rawValue = frame[key];
      const value = Number.isFinite(rawValue) ? (rawValue as number) : 0;
			return {
				frame: frame.frame_number,
				value,
			};
		});
  };

  const getMetricColor = (metric: string) => {
    const colors = {
      elbow: SHOOTRZ_THEME.colors.primary,
      knee: SHOOTRZ_THEME.colors.secondary,
      release: SHOOTRZ_THEME.colors.accent,
      alignment: SHOOTRZ_THEME.colors.warning,
    };
    return colors[metric as keyof typeof colors] || SHOOTRZ_THEME.colors.primary;
  };

  const getMetricName = (metric: string) => {
    const names = {
      elbow: 'Elbow Angle',
      knee: 'Knee Angle',
      release: 'Release Angle',
      alignment: 'Body Alignment',
    };
    return names[metric as keyof typeof names] || metric;
  };

  const getOptimalRange = (metric: string) => {
    const ranges = {
      elbow: { min: 85, max: 95, ideal: 90 },
      knee: { min: 120, max: 140, ideal: 130 },
      release: { min: 45, max: 50, ideal: 47.5 },
      alignment: { min: 80, max: 100, ideal: 90 },
    };
    return ranges[metric as keyof typeof ranges] || { min: 0, max: 100, ideal: 50 };
  };

  const renderGraph = () => {
    const data = getMetricData(selectedMetric);
    const optimalRange = getOptimalRange(selectedMetric);
    const color = getMetricColor(selectedMetric);

    if (data.length === 0) return null;

    const numericValues = data.map((d) => d.value).filter((v) => Number.isFinite(v));
    const baseMax = numericValues.length > 0 ? Math.max(...numericValues) : optimalRange.max ?? 100;
    const baseMin = numericValues.length > 0 ? Math.min(...numericValues) : optimalRange.min ?? 0;
    const paddedMax = Math.max(baseMax, optimalRange.max ?? baseMax);
    const paddedMin = Math.min(baseMin, optimalRange.min ?? baseMin);
    const rawRange = Math.max(paddedMax - paddedMin, 1);
    const padding = rawRange * 0.1;
    const maxValue = paddedMax + padding;
    const minValue = Math.max(0, paddedMin - padding);
    const valueRange = Math.max(maxValue - minValue, 1);

    // Use measured width from layout to fit container
    const effectiveGraphWidth = Math.max(graphWidth - yAxisWidth - SHOOTRZ_THEME.spacing.sm, 200);
    const graphHeight = 200;

    return (
      <View
        style={styles.graphContainer}
        onLayout={(evt: LayoutChangeEvent) => {
          const { width } = evt.nativeEvent.layout;
          setGraphWidth(width);
        }}
      >
        {/* Y-axis labels */}
        <View style={styles.yAxisContainer}>
          <Text style={styles.yAxisLabel}>{maxValue.toFixed(0)}</Text>
          <Text style={styles.yAxisLabel}>{((maxValue + minValue) / 2).toFixed(0)}</Text>
          <Text style={styles.yAxisLabel}>{minValue.toFixed(0)}</Text>
        </View>

        {/* Graph area */}
        <View style={[styles.graphArea, { width: effectiveGraphWidth, height: graphHeight }]}>
          {/* Optimal range background */}
          <View
            style={[
              styles.optimalRange,
              {
                top: (() => {
                  const visualMax = Math.min(Math.max(optimalRange.max, minValue), maxValue);
                  return ((maxValue - visualMax) / valueRange) * graphHeight;
                })(),
                height: (() => {
                  const visualMin = Math.min(Math.max(optimalRange.min, minValue), maxValue);
                  const visualMax = Math.max(
                    visualMin + 0.5,
                    Math.min(optimalRange.max, maxValue)
                  );
                  return Math.max(((visualMax - visualMin) / valueRange) * graphHeight, 2);
                })(),
              },
            ]}
          />

          {/* Data line */}
          <View style={styles.dataLine}>
            {data.map((point, index) => {
              const x = (index / Math.max(data.length - 1, 1)) * effectiveGraphWidth;
              const y = ((maxValue - point.value) / valueRange) * graphHeight;

              return (
                <TouchableOpacity
                  key={index}
                  style={[
                    styles.dataPoint,
                    {
                      left: x - 4,
                      top: y - 4,
                      backgroundColor: color,
                      borderColor:
                        selectedFrame === point.frame ? SHOOTRZ_THEME.colors.textPrimary : 'transparent',
                      borderWidth: selectedFrame === point.frame ? 2 : 0,
                    },
                  ]}
                  onPress={() => onFrameSelect?.(point.frame)}
                />
              );
            })}
          </View>

          {/* Optimal line */}
          <View
            style={[
              styles.optimalLine,
              {
                top: (() => {
                  const ideal = Math.min(Math.max(optimalRange.ideal, minValue), maxValue);
                  return ((maxValue - ideal) / valueRange) * graphHeight;
                })(),
                backgroundColor: color,
              },
            ]}
          />
        </View>

        {/* X-axis labels */}
        <View style={styles.xAxisContainer}>
          <Text style={styles.xAxisLabel}>Start</Text>
          <Text style={styles.xAxisLabel}>Mid</Text>
          <Text style={styles.xAxisLabel}>End</Text>
        </View>
      </View>
    );
  };

  return (
    <View style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.title}>Angle Consistency</Text>
        <TouchableOpacity
          style={styles.toggleButton}
          onPress={() => setShowAllMetrics(!showAllMetrics)}
        >
          <Ionicons
            name={showAllMetrics ? 'eye-off' : 'eye'}
            size={20}
            color={SHOOTRZ_THEME.colors.primary}
          />
          <Text style={styles.toggleText}>{showAllMetrics ? 'Single' : 'All'}</Text>
        </TouchableOpacity>
      </View>

      {/* Metric selector */}
      {!showAllMetrics && availableMetrics.length > 0 && (
        <View style={styles.metricSelector}>
          {availableMetrics.map((metric) => (
            <TouchableOpacity
              key={metric}
              style={[styles.metricButton, selectedMetric === metric && styles.metricButtonActive]}
              onPress={() => setSelectedMetric(metric)}
            >
              <Text
                style={[
                  styles.metricButtonText,
                  selectedMetric === metric && styles.metricButtonTextActive,
                ]}
              >
                {getMetricName(metric)}
              </Text>
            </TouchableOpacity>
          ))}
        </View>
      )}

      {/* Graph */}
      {renderGraph()}

      {/* Legend */}
      <View style={styles.legend}>
        <View style={styles.legendItem}>
          <View style={[styles.legendColor, { backgroundColor: getMetricColor(selectedMetric) }]} />
          <Text style={styles.legendText}>{getMetricName(selectedMetric)}</Text>
        </View>
        <View style={styles.legendItem}>
          <View
            style={[
              styles.legendColor,
              { backgroundColor: SHOOTRZ_THEME.colors.success, opacity: 0.3 },
            ]}
          />
          <Text style={styles.legendText}>Optimal Range</Text>
        </View>
      </View>

      {/* Stats */}
      <View style={styles.stats}>
        <View style={styles.statItem}>
          <Text style={styles.statLabel}>Consistency</Text>
          <Text style={styles.statValue}>
            {(() => {
              const data = getMetricData(selectedMetric);
              const values = data.map((d) => d.value).filter((v) => Number.isFinite(v));
              if (values.length === 0) return '--%';
              const mean = values.reduce((a, b) => a + b, 0) / values.length || 1;
              const variance =
                values.reduce((a, b) => a + Math.pow(b - mean, 2), 0) / values.length;
              const stdDev = Math.sqrt(variance);
              const consistency = Math.max(0, Math.min(100, 100 - (stdDev / mean) * 100));
              return consistency.toFixed(1) + '%';
            })()}
          </Text>
        </View>
        <View style={styles.statItem}>
          <Text style={styles.statLabel}>Average</Text>
          <Text style={styles.statValue}>
            {(() => {
              const data = getMetricData(selectedMetric);
              const values = data.map((d) => d.value).filter((v) => Number.isFinite(v));
              if (values.length === 0) return '--';
              const avg = values.reduce((a, b) => a + b, 0) / values.length;
              return avg.toFixed(1) + '°';
            })()}
          </Text>
        </View>
        <View style={styles.statItem}>
          <Text style={styles.statLabel}>Range</Text>
          <Text style={styles.statValue}>
            {(() => {
              const data = getMetricData(selectedMetric);
              const values = data.map((d) => d.value).filter((v) => Number.isFinite(v));
              if (values.length === 0) return '--';
              const min = Math.min(...values);
              const max = Math.max(...values);
              return (max - min).toFixed(1) + '°';
            })()}
          </Text>
        </View>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: SHOOTRZ_THEME.colors.surface,
    borderRadius: SHOOTRZ_THEME.borderRadius.lg,
    padding: SHOOTRZ_THEME.spacing.md,
    marginVertical: SHOOTRZ_THEME.spacing.sm,
  },
  emptyContainer: {
    alignItems: 'center',
    padding: SHOOTRZ_THEME.spacing.xl,
  },
  emptyText: {
    fontSize: 16,
    color: SHOOTRZ_THEME.colors.textSecondary,
    marginTop: SHOOTRZ_THEME.spacing.sm,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: SHOOTRZ_THEME.spacing.md,
  },
  title: {
    fontSize: 18,
    fontWeight: '700',
    color: SHOOTRZ_THEME.colors.textPrimary,
  },
  toggleButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: SHOOTRZ_THEME.spacing.sm,
    paddingVertical: SHOOTRZ_THEME.spacing.xs,
    borderRadius: SHOOTRZ_THEME.borderRadius.sm,
    backgroundColor: SHOOTRZ_THEME.colors.surfaceElevated,
  },
  toggleText: {
    fontSize: 14,
    color: SHOOTRZ_THEME.colors.primary,
    marginLeft: 4,
    fontWeight: '500',
  },
  metricSelector: {
    flexDirection: 'row',
    marginBottom: SHOOTRZ_THEME.spacing.md,
  },
  metricButton: {
    flex: 1,
    paddingVertical: SHOOTRZ_THEME.spacing.sm,
    paddingHorizontal: SHOOTRZ_THEME.spacing.xs,
    borderRadius: SHOOTRZ_THEME.borderRadius.sm,
    backgroundColor: SHOOTRZ_THEME.colors.surfaceElevated,
    marginHorizontal: 2,
    alignItems: 'center',
  },
  metricButtonActive: {
    backgroundColor: SHOOTRZ_THEME.colors.primary,
  },
  metricButtonText: {
    fontSize: 12,
    color: SHOOTRZ_THEME.colors.textSecondary,
    fontWeight: '500',
  },
  metricButtonTextActive: {
    color: SHOOTRZ_THEME.colors.surface,
  },
  graphContainer: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    marginBottom: SHOOTRZ_THEME.spacing.md,
  },
  yAxisContainer: {
    width: 30,
    justifyContent: 'space-between',
    height: 200,
    paddingVertical: 10,
  },
  yAxisLabel: {
    fontSize: 12,
    color: SHOOTRZ_THEME.colors.textSecondary,
    textAlign: 'right',
  },
  graphArea: {
    position: 'relative',
    backgroundColor: SHOOTRZ_THEME.colors.surfaceElevated,
    borderRadius: SHOOTRZ_THEME.borderRadius.sm,
    marginLeft: SHOOTRZ_THEME.spacing.sm,
    overflow: 'hidden',
  },
  optimalRange: {
    position: 'absolute',
    left: 0,
    right: 0,
    backgroundColor: SHOOTRZ_THEME.colors.success,
    opacity: 0.2,
    borderRadius: SHOOTRZ_THEME.borderRadius.sm,
  },
  dataLine: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
  },
  dataPoint: {
    position: 'absolute',
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  optimalLine: {
    position: 'absolute',
    left: 0,
    right: 0,
    height: 2,
    opacity: 0.8,
  },
  xAxisContainer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginLeft: 40,
    marginTop: SHOOTRZ_THEME.spacing.sm,
  },
  xAxisLabel: {
    fontSize: 12,
    color: SHOOTRZ_THEME.colors.textSecondary,
  },
  legend: {
    flexDirection: 'row',
    justifyContent: 'center',
    marginBottom: SHOOTRZ_THEME.spacing.md,
  },
  legendItem: {
    flexDirection: 'row',
    alignItems: 'center',
    marginHorizontal: SHOOTRZ_THEME.spacing.sm,
  },
  legendColor: {
    width: 12,
    height: 12,
    borderRadius: 6,
    marginRight: 4,
  },
  legendText: {
    fontSize: 12,
    color: SHOOTRZ_THEME.colors.textSecondary,
  },
  stats: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    paddingTop: SHOOTRZ_THEME.spacing.sm,
    borderTopWidth: 1,
    borderTopColor: SHOOTRZ_THEME.colors.surfaceElevated,
  },
  statItem: {
    alignItems: 'center',
  },
  statLabel: {
    fontSize: 12,
    color: SHOOTRZ_THEME.colors.textSecondary,
    marginBottom: 2,
  },
  statValue: {
    fontSize: 16,
    fontWeight: '700',
    color: SHOOTRZ_THEME.colors.textPrimary,
  },
});
