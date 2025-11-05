/**
 * Central icon mapping utility for consistent icon usage across the app
 * Maps semantic names to Ionicons icon names
 */

export type IconName = 
  | 'basketball'
  | 'video'
  | 'fitness'
  | 'chat'
  | 'stats'
  | 'target'
  | 'time'
  | 'flash'
  | 'shield'
  | 'walk'
  | 'flame'
  | 'trophy'
  | 'checkmark'
  | 'folder'
  | 'search'
  | 'people'
  | 'mail'
  | 'info'
  | 'close'
  | 'help'
  | 'trash'
  | 'lock'
  | 'person'
  | 'document'
  | 'calendar'
  | 'shooting'
  | 'dribbling'
  | 'defense'
  | 'conditioning';

/**
 * Get the appropriate Ionicons name for a semantic icon
 */
export const getIconName = (icon: IconName): string => {
  const iconMap: Record<IconName, string> = {
    basketball: 'basketball',
    video: 'videocam',
    fitness: 'barbell',
    chat: 'chatbubbles',
    stats: 'stats-chart',
    target: 'target',
    time: 'time',
    flash: 'flash',
    shield: 'shield',
    walk: 'walk',
    flame: 'flame',
    trophy: 'trophy',
    checkmark: 'checkmark-circle',
    folder: 'folder',
    search: 'search',
    people: 'people',
    mail: 'mail',
    info: 'information-circle',
    close: 'close-circle',
    help: 'help-circle',
    trash: 'trash',
    lock: 'lock-closed',
    person: 'person',
    document: 'document-text',
    calendar: 'calendar',
    // Drill categories
    shooting: 'basketball',
    dribbling: 'flash',
    defense: 'shield',
    conditioning: 'barbell',
  };

  return iconMap[icon] || 'help-circle';
};

/**
 * Get icon name for drill category
 */
export const getDrillCategoryIcon = (category: string): string => {
  const categoryMap: Record<string, string> = {
    shooting: 'basketball',
    dribbling: 'flash',
    defense: 'shield',
    conditioning: 'barbell',
    footwork: 'walk',
  };

  return categoryMap[category.toLowerCase()] || 'fitness';
};

/**
 * Get icon name for activity type
 */
export const getActivityIcon = (activityType: string): string => {
  const activityMap: Record<string, string> = {
    Analysis: 'stats-chart',
    Drill: 'basketball',
    Workout: 'barbell',
    Practice: 'time',
  };

  return activityMap[activityType] || 'fitness';
};

