import React, { useState } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, FlatList, Modal, ColorValue } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { SafeAreaView } from 'react-native-safe-area-context';
import { DrillCard } from '../components/DrillCard';
import { EmptyState } from '../components/EmptyState';
import { DRILLS, Drill } from '../constants/drills';
import { SHOOTRZ_THEME, COMPONENT_STYLES } from '../constants/theme';
import { DrillDetailScreen } from './DrillDetailScreen';

export const DrillsScreen: React.FC = () => {
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [selectedDifficulty, setSelectedDifficulty] = useState<string>('all');
  const [selectedDrill, setSelectedDrill] = useState<Drill | null>(null);

  const categories = ['all', 'shooting', 'dribbling', 'defense', 'conditioning'];
  const difficulties = ['all', 'beginner', 'intermediate', 'advanced'];

  const filteredDrills = DRILLS.filter(drill => {
    const categoryMatch = selectedCategory === 'all' || drill.category === selectedCategory;
    const difficultyMatch = selectedDifficulty === 'all' || drill.difficulty === selectedDifficulty;
    return categoryMatch && difficultyMatch;
  });

  const handleDrillPress = (drill: Drill) => {
    setSelectedDrill(drill);
  };

  const renderDrill = ({ item }: { item: Drill }) => (
    <DrillCard drill={item} onPress={() => handleDrillPress(item)} />
  );

  return (
    <SafeAreaView style={styles.container} edges={['top', 'left', 'right']}>
      <View style={styles.header}>
        <Text style={styles.title}>Training Drills</Text>
        <Text style={styles.subtitle}>Improve your skills with targeted exercises</Text>
      </View>

      {/* Combined Filters */}
      <View style={styles.combinedFiltersSection}>
        {/* Category Filter */}
        <View style={styles.filterRow}>
          <Text style={styles.filterLabel}>Category:</Text>
          <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.filterScroll}>
            {categories.map((category) => (
              selectedCategory === category ? (
                <LinearGradient
                  key={category}
                  colors={SHOOTRZ_THEME.gradients.primary as [ColorValue, ColorValue]}
                  start={{ x: 0, y: 0 }}
                  end={{ x: 1, y: 0 }}
                  style={[styles.compactFilterButton, styles.activeCompactFilterButton]}
                >
                  <TouchableOpacity onPress={() => setSelectedCategory(category)}>
                    <Text style={styles.activeCompactFilterButtonText}>
                      {category.charAt(0).toUpperCase() + category.slice(1)}
                    </Text>
                  </TouchableOpacity>
                </LinearGradient>
              ) : (
                <TouchableOpacity
                  key={category}
                  style={styles.compactFilterButton}
                  onPress={() => setSelectedCategory(category)}
                >
                  <Text style={styles.compactFilterButtonText}>
                    {category.charAt(0).toUpperCase() + category.slice(1)}
                  </Text>
                </TouchableOpacity>
              )
            ))}
          </ScrollView>
        </View>

        {/* Difficulty Filter */}
        <View style={styles.filterRow}>
          <Text style={styles.filterLabel}>Difficulty:</Text>
          <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.filterScroll}>
            {difficulties.map((difficulty) => (
              selectedDifficulty === difficulty ? (
                <LinearGradient
                  key={difficulty}
                  colors={SHOOTRZ_THEME.gradients.secondary as [ColorValue, ColorValue]}
                  start={{ x: 0, y: 0 }}
                  end={{ x: 1, y: 0 }}
                  style={[styles.compactFilterButton, styles.activeCompactFilterButton]}
                >
                  <TouchableOpacity onPress={() => setSelectedDifficulty(difficulty)}>
                    <Text style={styles.activeCompactFilterButtonText}>
                      {difficulty.charAt(0).toUpperCase() + difficulty.slice(1)}
                    </Text>
                  </TouchableOpacity>
                </LinearGradient>
              ) : (
                <TouchableOpacity
                  key={difficulty}
                  style={styles.compactFilterButton}
                  onPress={() => setSelectedDifficulty(difficulty)}
                >
                  <Text style={styles.compactFilterButtonText}>
                    {difficulty.charAt(0).toUpperCase() + difficulty.slice(1)}
                  </Text>
                </TouchableOpacity>
              )
            ))}
          </ScrollView>
        </View>
      </View>

      {/* Results Count */}
      <View style={styles.resultsHeader}>
        <Text style={styles.resultsCount}>
          {filteredDrills.length} drill{filteredDrills.length !== 1 ? 's' : ''} found
        </Text>
      </View>

      {/* Drills List */}
      {filteredDrills.length === 0 ? (
        <EmptyState
          icon="🔍"
          title="No Drills Found"
          message="Try adjusting your filters to see more drills"
          actionText="Clear Filters"
          onAction={() => {
            setSelectedCategory('all');
            setSelectedDifficulty('all');
          }}
        />
      ) : (
        <FlatList
          data={filteredDrills}
          renderItem={renderDrill}
          keyExtractor={(item) => item.id}
          contentContainerStyle={styles.drillsList}
          showsVerticalScrollIndicator={false}
        />
      )}

      {/* Drill Detail Modal */}
      <Modal
        visible={selectedDrill !== null}
        animationType="slide"
        presentationStyle="fullScreen"
        onRequestClose={() => setSelectedDrill(null)}
      >
        {selectedDrill && (
          <DrillDetailScreen
            drill={selectedDrill}
            onClose={() => setSelectedDrill(null)}
          />
        )}
      </Modal>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: SHOOTRZ_THEME.colors.background,
  },
  header: {
    padding: SHOOTRZ_THEME.spacing.lg,
    backgroundColor: SHOOTRZ_THEME.colors.surface,
    borderBottomWidth: 1,
    borderBottomColor: SHOOTRZ_THEME.colors.surfaceElevated,
  },
  title: {
    ...SHOOTRZ_THEME.typography.heading2,
    marginBottom: SHOOTRZ_THEME.spacing.xs,
  },
  subtitle: {
    ...SHOOTRZ_THEME.typography.body,
    color: SHOOTRZ_THEME.colors.textSecondary,
  },
  combinedFiltersSection: {
    padding: SHOOTRZ_THEME.spacing.md,
    backgroundColor: SHOOTRZ_THEME.colors.surface,
    borderBottomWidth: 1,
    borderBottomColor: SHOOTRZ_THEME.colors.surfaceElevated,
  },
  filterRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: SHOOTRZ_THEME.spacing.sm,
  },
  filterLabel: {
    ...SHOOTRZ_THEME.typography.bodySmall,
    fontWeight: '600',
    color: SHOOTRZ_THEME.colors.textSecondary,
    marginRight: SHOOTRZ_THEME.spacing.sm,
    minWidth: 70,
  },
  filterScroll: {
    flexDirection: 'row',
  },
  filterButton: {
    paddingHorizontal: SHOOTRZ_THEME.spacing.md,
    paddingVertical: SHOOTRZ_THEME.spacing.sm,
    borderRadius: SHOOTRZ_THEME.borderRadius.xl,
    backgroundColor: SHOOTRZ_THEME.colors.surfaceElevated,
    marginRight: SHOOTRZ_THEME.spacing.sm,
    overflow: 'hidden',
  },
  activeFilterButton: {
    backgroundColor: 'transparent',
  },
  filterButtonText: {
    ...SHOOTRZ_THEME.typography.bodySmall,
    color: SHOOTRZ_THEME.colors.textSecondary,
    fontWeight: '500',
  },
  activeFilterButtonText: {
    color: SHOOTRZ_THEME.colors.textPrimary,
  },
  compactFilterButton: {
    paddingHorizontal: SHOOTRZ_THEME.spacing.sm,
    paddingVertical: SHOOTRZ_THEME.spacing.xs,
    borderRadius: SHOOTRZ_THEME.borderRadius.lg,
    backgroundColor: SHOOTRZ_THEME.colors.surfaceElevated,
    marginRight: SHOOTRZ_THEME.spacing.xs,
    overflow: 'hidden',
  },
  activeCompactFilterButton: {
    backgroundColor: 'transparent',
  },
  compactFilterButtonText: {
    ...SHOOTRZ_THEME.typography.caption,
    color: SHOOTRZ_THEME.colors.textSecondary,
    fontWeight: '500',
  },
  activeCompactFilterButtonText: {
    ...SHOOTRZ_THEME.typography.caption,
    color: SHOOTRZ_THEME.colors.textPrimary,
    fontWeight: '600',
  },
  resultsHeader: {
    padding: SHOOTRZ_THEME.spacing.md,
    backgroundColor: SHOOTRZ_THEME.colors.surface,
  },
  resultsCount: {
    ...SHOOTRZ_THEME.typography.bodySmall,
    color: SHOOTRZ_THEME.colors.textSecondary,
  },
  drillsList: {
    padding: SHOOTRZ_THEME.spacing.md,
  },
});
