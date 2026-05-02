import { useMemo, useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import Card from '../components/Card';
import FadeInView from '../components/FadeInView';
import PrimaryButton from '../components/PrimaryButton';
import Screen from '../components/Screen';
import {
  ALLERGEN_OPTIONS,
  CONDITION_OPTIONS,
  HealthOption,
  useHealthPreferences,
} from '../state/HealthPreferencesContext';
import { AppTheme, radii, spacing, useAppTheme } from '../theme';

function OptionChip({
  option,
  selected,
  onPress,
  theme,
}: {
  option: HealthOption;
  selected: boolean;
  onPress: () => void;
  theme: AppTheme;
}) {
  const styles = useMemo(() => createStyles(theme), [theme]);

  return (
    <Pressable
      accessibilityRole="button"
      accessibilityState={{ selected }}
      onPress={onPress}
      style={({ pressed }) => [
        styles.chip,
        selected && styles.chipSelected,
        pressed && styles.chipPressed,
      ]}
    >
      <Text style={[styles.chipLabel, selected && styles.chipLabelSelected]}>{option.label}</Text>
      <Text style={[styles.chipDescription, selected && styles.chipDescriptionSelected]}>
        {option.description}
      </Text>
    </Pressable>
  );
}

function toggleList(values: string[], nextValue: string): string[] {
  return values.includes(nextValue)
    ? values.filter((value) => value !== nextValue)
    : [...values, nextValue];
}

export default function HealthScreen() {
  const theme = useAppTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);
  const sharedStyles = theme.sharedStyles;
  const {
    activeCount,
    activeProfile,
    profiles,
    profilesLoading,
    selectedAllergens,
    selectedConditions,
    toggleAllergen,
    toggleCondition,
    isAllergenSelected,
    isConditionSelected,
    selectProfile,
    createProfile,
    updateProfile,
    deleteProfile,
    clearPreferences,
  } = useHealthPreferences();

  const [editingProfileId, setEditingProfileId] = useState<number | null>(null);
  const [draftName, setDraftName] = useState('');
  const [draftNotes, setDraftNotes] = useState('');
  const [draftAllergies, setDraftAllergies] = useState<string[]>([]);
  const [draftConditions, setDraftConditions] = useState<string[]>([]);
  const [draftDefault, setDraftDefault] = useState(false);
  const [saving, setSaving] = useState(false);

  const currentSummary = useMemo(() => {
    if (!activeCount) {
      return 'No current checks active';
    }

    const allergenSummary = selectedAllergens.length ? selectedAllergens.join(', ') : 'no allergens';
    const conditionSummary = selectedConditions.length ? selectedConditions.join(', ') : 'no conditions';
    return `${allergenSummary} • ${conditionSummary}`;
  }, [activeCount, selectedAllergens, selectedConditions]);

  function startNewProfile() {
    setEditingProfileId(null);
    setDraftName('');
    setDraftNotes('');
    setDraftAllergies([...selectedAllergens]);
    setDraftConditions([...selectedConditions]);
    setDraftDefault(profiles.length === 0);
  }

  function startEditProfile(profileId: number) {
    const profile = profiles.find((item) => item.id === profileId);
    if (!profile) {
      return;
    }
    setEditingProfileId(profile.id);
    setDraftName(profile.name);
    setDraftNotes(profile.notes || '');
    setDraftAllergies([...profile.allergies]);
    setDraftConditions([...profile.conditions]);
    setDraftDefault(profile.is_default);
  }

  async function handleSaveProfile() {
    if (!draftName.trim()) {
      Alert.alert('Profiles', 'Profile name is required.');
      return;
    }

    try {
      setSaving(true);
      const payload = {
        name: draftName.trim(),
        notes: draftNotes.trim(),
        allergies: draftAllergies,
        conditions: draftConditions,
        is_default: draftDefault,
      };

      if (editingProfileId) {
        await updateProfile(editingProfileId, payload);
      } else {
        await createProfile(payload);
      }

      startNewProfile();
    } catch {
      Alert.alert('Profiles', 'Unable to save this profile right now.');
    } finally {
      setSaving(false);
    }
  }

  async function handleDeleteProfile(profileId: number) {
    Alert.alert('Delete profile', 'This removes the saved profile but keeps your product data untouched.', [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Delete',
        style: 'destructive',
        onPress: async () => {
          try {
            await deleteProfile(profileId);
            if (editingProfileId === profileId) {
              startNewProfile();
            }
          } catch {
            Alert.alert('Profiles', 'Unable to delete this profile right now.');
          }
        },
      },
    ]);
  }

  return (
    <Screen>
      <FadeInView>
        <Text style={sharedStyles.screenTitle}>Health</Text>
        <Text style={styles.subtitle}>
          Saved profiles keep the app ready for daily use. Session tweaks stay easy to adjust before you commit them.
        </Text>
      </FadeInView>

      <FadeInView delay={40}>
        <Card style={styles.card}>
          <View style={styles.cardHeader}>
            <Text style={sharedStyles.sectionTitle}>Current checks</Text>
            {activeCount > 0 ? <Text style={styles.healthBadge}>{activeCount} active</Text> : null}
          </View>
          <Text style={sharedStyles.footnote}>
            {activeProfile ? `Using profile ${activeProfile.name}` : 'No saved profile selected'}
          </Text>
          <Text style={styles.summary}>{currentSummary}</Text>

          <Text style={styles.label}>Conditions</Text>
          <View style={styles.optionGrid}>
            {CONDITION_OPTIONS.map((option) => (
              <OptionChip
                key={option.key}
                onPress={() => toggleCondition(option.queryValue)}
                option={option}
                selected={isConditionSelected(option.queryValue)}
                theme={theme}
              />
            ))}
          </View>

          <Text style={styles.label}>Allergens</Text>
          <View style={styles.optionGrid}>
            {ALLERGEN_OPTIONS.map((option) => (
              <OptionChip
                key={option.key}
                onPress={() => toggleAllergen(option.queryValue)}
                option={option}
                selected={isAllergenSelected(option.queryValue)}
                theme={theme}
              />
            ))}
          </View>

          <View style={styles.actionRow}>
            <PrimaryButton onPress={startNewProfile} style={styles.actionButton} variant="secondary">
              Save as profile
            </PrimaryButton>
            <PrimaryButton disabled={activeCount === 0} onPress={clearPreferences} style={styles.actionButton} variant="quiet">
              Clear
            </PrimaryButton>
          </View>
        </Card>
      </FadeInView>

      <FadeInView delay={80}>
        <Card style={styles.card}>
          <View style={styles.cardHeader}>
            <Text style={sharedStyles.sectionTitle}>Saved profiles</Text>
            <PrimaryButton onPress={startNewProfile} variant="quiet">
              New
            </PrimaryButton>
          </View>

          {profilesLoading ? (
            <View style={styles.loaderRow}>
              <ActivityIndicator color={theme.colors.accent} />
            </View>
          ) : profiles.length ? (
            <View style={styles.profileStack}>
              {profiles.map((profile) => (
                <View key={profile.id} style={styles.profileRow}>
                  <View style={styles.profileCopy}>
                    <View style={styles.profileTitleRow}>
                      <Text style={styles.profileName}>{profile.name}</Text>
                      {profile.is_default ? <Text style={styles.defaultPill}>Default</Text> : null}
                      {activeProfile?.id === profile.id ? <Text style={styles.activePill}>Active</Text> : null}
                    </View>
                    <Text style={sharedStyles.footnote}>
                      {(profile.allergies.length ? profile.allergies.join(', ') : 'No allergies')} • {(profile.conditions.length ? profile.conditions.join(', ') : 'No conditions')}
                    </Text>
                    {profile.notes ? <Text style={styles.profileNotes}>{profile.notes}</Text> : null}
                  </View>
                  <View style={styles.profileActions}>
                    <PrimaryButton onPress={() => selectProfile(profile.id)} variant="secondary">
                      Use
                    </PrimaryButton>
                    <PrimaryButton onPress={() => startEditProfile(profile.id)} variant="quiet">
                      Edit
                    </PrimaryButton>
                    <PrimaryButton onPress={() => handleDeleteProfile(profile.id)} variant="quiet">
                      Delete
                    </PrimaryButton>
                  </View>
                </View>
              ))}
            </View>
          ) : (
            <Text style={sharedStyles.body}>No saved profiles yet. Save the current checks to avoid re-entering them every time.</Text>
          )}
        </Card>
      </FadeInView>

      <FadeInView delay={120}>
        <Card style={styles.card}>
          <Text style={sharedStyles.sectionTitle}>
            {editingProfileId ? 'Edit profile' : 'Create profile'}
          </Text>
          <TextInput
            onChangeText={setDraftName}
            placeholder="Profile name"
            placeholderTextColor={theme.colors.muted}
            style={styles.input}
            value={draftName}
          />
          <TextInput
            multiline
            onChangeText={setDraftNotes}
            placeholder="Notes (optional)"
            placeholderTextColor={theme.colors.muted}
            style={[styles.input, styles.notesInput]}
            value={draftNotes}
          />

          <Pressable
            accessibilityRole="button"
            onPress={() => setDraftDefault((current) => !current)}
            style={[styles.toggleRow, draftDefault && styles.toggleRowActive]}
          >
            <Text style={styles.toggleTitle}>Set as default profile</Text>
            <Text style={styles.toggleValue}>{draftDefault ? 'Yes' : 'No'}</Text>
          </Pressable>

          <Text style={styles.label}>Profile conditions</Text>
          <View style={styles.optionGrid}>
            {CONDITION_OPTIONS.map((option) => (
              <OptionChip
                key={`profile-${option.key}`}
                onPress={() => setDraftConditions((current) => toggleList(current, option.queryValue))}
                option={option}
                selected={draftConditions.includes(option.queryValue)}
                theme={theme}
              />
            ))}
          </View>

          <Text style={styles.label}>Profile allergens</Text>
          <View style={styles.optionGrid}>
            {ALLERGEN_OPTIONS.map((option) => (
              <OptionChip
                key={`profile-${option.key}`}
                onPress={() => setDraftAllergies((current) => toggleList(current, option.queryValue))}
                option={option}
                selected={draftAllergies.includes(option.queryValue)}
                theme={theme}
              />
            ))}
          </View>

          <View style={styles.actionRow}>
            <PrimaryButton loading={saving} onPress={handleSaveProfile} style={styles.actionButton}>
              {editingProfileId ? 'Update profile' : 'Create profile'}
            </PrimaryButton>
            <PrimaryButton onPress={startNewProfile} style={styles.actionButton} variant="quiet">
              Reset
            </PrimaryButton>
          </View>
        </Card>
      </FadeInView>
    </Screen>
  );
}

function createStyles(theme: AppTheme) {
  return StyleSheet.create({
    subtitle: {
      color: theme.colors.muted,
      fontSize: 15,
      lineHeight: 21,
      marginTop: spacing.sm,
      marginBottom: spacing.xl,
    },
    card: {
      marginBottom: spacing.md,
    },
    cardHeader: {
      alignItems: 'center',
      flexDirection: 'row',
      justifyContent: 'space-between',
      marginBottom: spacing.sm,
    },
    healthBadge: {
      backgroundColor: theme.colors.accentSoft,
      borderRadius: radii.pill,
      color: theme.colors.accent,
      fontSize: 12,
      fontWeight: '800',
      overflow: 'hidden',
      paddingHorizontal: 12,
      paddingVertical: 7,
    },
    summary: {
      color: theme.colors.text,
      fontSize: 14,
      lineHeight: 20,
      marginBottom: spacing.md,
      marginTop: spacing.sm,
    },
    label: {
      color: theme.colors.text,
      fontSize: 14,
      fontWeight: '700',
      marginBottom: spacing.sm,
      marginTop: spacing.md,
    },
    optionGrid: {
      gap: spacing.sm,
    },
    chip: {
      backgroundColor: theme.colors.surfaceMuted,
      borderColor: theme.colors.border,
      borderRadius: radii.md,
      borderWidth: 1,
      paddingHorizontal: 14,
      paddingVertical: 12,
    },
    chipSelected: {
      backgroundColor: theme.colors.accentSoft,
      borderColor: theme.colors.accent,
    },
    chipPressed: {
      opacity: 0.82,
      transform: [{ scale: 0.99 }],
    },
    chipLabel: {
      color: theme.colors.ink,
      fontSize: 16,
      fontWeight: '800',
      marginBottom: 4,
    },
    chipLabelSelected: {
      color: theme.colors.accent,
    },
    chipDescription: {
      color: theme.colors.muted,
      fontSize: 13,
      lineHeight: 18,
    },
    chipDescriptionSelected: {
      color: theme.colors.text,
    },
    actionRow: {
      flexDirection: 'row',
      gap: spacing.sm,
      marginTop: spacing.md,
    },
    actionButton: {
      flex: 1,
    },
    loaderRow: {
      alignItems: 'center',
      justifyContent: 'center',
      minHeight: 80,
    },
    profileStack: {
      gap: spacing.md,
    },
    profileRow: {
      borderTopColor: theme.colors.border,
      borderTopWidth: StyleSheet.hairlineWidth,
      paddingTop: spacing.md,
    },
    profileCopy: {
      marginBottom: spacing.md,
    },
    profileTitleRow: {
      alignItems: 'center',
      flexDirection: 'row',
      flexWrap: 'wrap',
      gap: spacing.sm,
      marginBottom: spacing.xs,
    },
    profileName: {
      color: theme.colors.ink,
      fontSize: 17,
      fontWeight: '700',
      lineHeight: 22,
    },
    defaultPill: {
      backgroundColor: theme.colors.accentSoft,
      borderRadius: radii.pill,
      color: theme.colors.accent,
      fontSize: 11,
      fontWeight: '800',
      overflow: 'hidden',
      paddingHorizontal: 9,
      paddingVertical: 4,
    },
    activePill: {
      backgroundColor: theme.colors.activeSurface,
      borderRadius: radii.pill,
      color: theme.colors.blue,
      fontSize: 11,
      fontWeight: '800',
      overflow: 'hidden',
      paddingHorizontal: 9,
      paddingVertical: 4,
    },
    profileNotes: {
      color: theme.colors.text,
      fontSize: 14,
      lineHeight: 20,
      marginTop: spacing.xs,
    },
    profileActions: {
      flexDirection: 'row',
      gap: spacing.sm,
    },
    input: {
      backgroundColor: theme.colors.inputBackground,
      borderColor: theme.colors.border,
      borderRadius: radii.md,
      borderWidth: 1,
      color: theme.colors.ink,
      fontSize: 16,
      marginTop: spacing.md,
      minHeight: 48,
      paddingHorizontal: 14,
      paddingVertical: 12,
    },
    notesInput: {
      minHeight: 88,
      textAlignVertical: 'top',
    },
    toggleRow: {
      alignItems: 'center',
      backgroundColor: theme.colors.surfaceMuted,
      borderColor: theme.colors.border,
      borderRadius: radii.md,
      borderWidth: 1,
      flexDirection: 'row',
      justifyContent: 'space-between',
      marginTop: spacing.md,
      paddingHorizontal: 14,
      paddingVertical: 12,
    },
    toggleRowActive: {
      borderColor: theme.colors.accent,
    },
    toggleTitle: {
      color: theme.colors.ink,
      fontSize: 15,
      fontWeight: '700',
    },
    toggleValue: {
      color: theme.colors.accent,
      fontSize: 14,
      fontWeight: '700',
    },
  });
}
