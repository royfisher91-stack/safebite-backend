import { useEffect, useMemo, useState } from 'react';
import { ActivityIndicator, Alert, StyleSheet, Text, TextInput, View } from 'react-native';
import Card from '../components/Card';
import FadeInView from '../components/FadeInView';
import PrimaryButton from '../components/PrimaryButton';
import ProductCard from '../components/ProductCard';
import Screen from '../components/Screen';
import { searchProducts } from '../api/client';
import { ProductSummary } from '../types/api';
import { MainTabScreenProps } from '../navigation/RootNavigator';
import { useHealthPreferences } from '../state/HealthPreferencesContext';
import { AppTheme, radii, spacing, useAppTheme } from '../theme';

type Props = MainTabScreenProps<'Search'>;

export default function SearchScreen({ navigation }: Props) {
  const theme = useAppTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);
  const sharedStyles = theme.sharedStyles;
  const [query, setQuery] = useState('Kendamil');
  const [results, setResults] = useState<ProductSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [hasSearched, setHasSearched] = useState(false);
  const {
    activeCount,
    activeProfile,
    activeProfileId,
    selectedAllergens,
    selectedConditions,
  } = useHealthPreferences();

  async function runSearch(nextQuery = query) {
    if (loading) {
      return;
    }

    const value = nextQuery.trim();
    setHasSearched(true);

    if (!value) {
      setResults([]);
      return;
    }

    try {
      setLoading(true);
      const data = await searchProducts(value, {
        allergens: selectedAllergens,
        conditions: selectedConditions,
        profileId: activeProfileId,
      });
      setResults(data);
    } catch {
      Alert.alert('Search failed', 'Check the SafeBite API is running.');
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    runSearch('Kendamil');
  }, []);

  const barcodeReady = /^[0-9]{6,}$/.test(query.trim());

  return (
    <Screen>
      <FadeInView>
        <View style={styles.titleRow}>
          <View style={styles.titleCopy}>
            <Text style={sharedStyles.screenTitle}>Search</Text>
            <Text style={styles.subtitle}>
              {activeProfile
                ? `Using ${activeProfile.name} for live results.`
                : activeCount > 0
                  ? 'Current session health checks are applied to results.'
                  : 'Search by food name or jump straight to a barcode.'}
            </Text>
          </View>
          {activeCount > 0 ? <Text style={styles.healthBadge}>{activeCount} active</Text> : null}
        </View>
      </FadeInView>

      <FadeInView delay={50}>
        <Card style={styles.searchCard}>
          <Text style={styles.label}>Food or barcode</Text>
          <TextInput
            autoCapitalize="none"
            autoCorrect={false}
            clearButtonMode="while-editing"
            onChangeText={setQuery}
            onSubmitEditing={() => runSearch()}
            placeholder="Search SafeBite"
            placeholderTextColor={theme.colors.muted}
            returnKeyType="search"
            style={styles.input}
            value={query}
          />
          <View style={styles.actions}>
            <PrimaryButton loading={loading} onPress={() => runSearch()} style={styles.actionButton}>
              Search
            </PrimaryButton>
            <PrimaryButton
              disabled={!barcodeReady}
              onPress={() =>
                navigation.navigate('ProductDetail', {
                  barcode: query.trim(),
                  shouldSaveHistory: true,
                })
              }
              style={styles.actionButton}
              variant="quiet"
            >
              Open barcode
            </PrimaryButton>
          </View>
        </Card>
      </FadeInView>

      {loading ? (
        <FadeInView delay={80} style={styles.loaderWrap}>
          <ActivityIndicator color={theme.colors.accent} size="large" />
        </FadeInView>
      ) : results.length > 0 ? (
        <View style={styles.results}>
          {results.map((product, index) => (
            <FadeInView delay={100 + index * 35} key={product.barcode}>
              <ProductCard
                product={product}
                onPress={() =>
                  navigation.navigate('ProductDetail', {
                    barcode: product.barcode,
                    shouldSaveHistory: true,
                  })
                }
              />
            </FadeInView>
          ))}
        </View>
      ) : hasSearched ? (
        <FadeInView delay={100}>
          <Card>
            <Text style={styles.emptyTitle}>No matching products found</Text>
            <Text style={sharedStyles.body}>
              Try a simpler name, or open a product directly if you already have the barcode.
            </Text>
          </Card>
        </FadeInView>
      ) : null}
    </Screen>
  );
}

function createStyles(theme: AppTheme) {
  return StyleSheet.create({
    titleRow: {
      alignItems: 'flex-start',
      flexDirection: 'row',
      gap: spacing.md,
      justifyContent: 'space-between',
    },
    titleCopy: {
      flex: 1,
    },
    subtitle: {
      color: theme.colors.muted,
      fontSize: 15,
      lineHeight: 22,
      marginTop: spacing.sm,
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
    searchCard: {
      marginTop: spacing.xl,
      marginBottom: spacing.lg,
    },
    label: {
      color: theme.colors.text,
      fontSize: 14,
      fontWeight: '700',
      marginBottom: spacing.sm,
    },
    input: {
      backgroundColor: theme.colors.inputBackground,
      borderColor: theme.colors.border,
      borderRadius: radii.md,
      borderWidth: 1,
      color: theme.colors.ink,
      fontSize: 17,
      minHeight: 54,
      paddingHorizontal: 16,
    },
    actions: {
      flexDirection: 'row',
      gap: spacing.sm,
      marginTop: spacing.md,
    },
    actionButton: {
      flex: 1,
    },
    loaderWrap: {
      alignItems: 'center',
      justifyContent: 'center',
      minHeight: 200,
    },
    results: {
      gap: spacing.md,
    },
    emptyTitle: {
      color: theme.colors.ink,
      fontSize: 18,
      fontWeight: '700',
      lineHeight: 24,
      marginBottom: spacing.sm,
    },
  });
}
