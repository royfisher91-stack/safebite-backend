import { useCallback, useMemo, useState } from 'react';
import { useFocusEffect } from '@react-navigation/native';
import { ActivityIndicator, Alert, Pressable, StyleSheet, Text, View } from 'react-native';
import Card from '../components/Card';
import FadeInView from '../components/FadeInView';
import PrimaryButton from '../components/PrimaryButton';
import ProductImage from '../components/ProductImage';
import Screen from '../components/Screen';
import StatusPill from '../components/StatusPill';
import {
  deleteFavourite,
  deleteHistoryEntry,
  getFavourites,
  getHistory,
} from '../api/client';
import { MainTabScreenProps } from '../navigation/RootNavigator';
import { Favourite, HistoryEntry } from '../types/api';
import { AppTheme, radii, spacing, useAppTheme } from '../theme';
import { formatDateTime, sentence } from '../utils/format';

type Props = MainTabScreenProps<'Saved'>;
type TabKey = 'favourites' | 'history';

export default function SavedScreen({ navigation }: Props) {
  const theme = useAppTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);
  const sharedStyles = theme.sharedStyles;
  const [tab, setTab] = useState<TabKey>('favourites');
  const [loading, setLoading] = useState(true);
  const [favourites, setFavourites] = useState<Favourite[]>([]);
  const [history, setHistory] = useState<HistoryEntry[]>([]);

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      const [nextFavourites, nextHistory] = await Promise.all([
        getFavourites(),
        getHistory(80),
      ]);
      setFavourites(nextFavourites);
      setHistory(nextHistory);
    } finally {
      setLoading(false);
    }
  }, []);

  useFocusEffect(
    useCallback(() => {
      loadData().catch(() => undefined);
    }, [loadData]),
  );

  async function handleRemoveFavourite(item: Favourite) {
    try {
      await deleteFavourite(item.id);
      setFavourites((current) => current.filter((entry) => entry.id !== item.id));
    } catch {
      Alert.alert('Saved items', 'Unable to remove this favourite right now.');
    }
  }

  async function handleDeleteHistory(item: HistoryEntry) {
    try {
      await deleteHistoryEntry(item.id);
      setHistory((current) => current.filter((entry) => entry.id !== item.id));
    } catch {
      Alert.alert('Scan history', 'Unable to remove this history row right now.');
    }
  }

  return (
    <Screen>
      <FadeInView>
        <Text style={sharedStyles.screenTitle}>Saved</Text>
        <Text style={styles.subtitle}>Favourites and recent checks stay ready for quick return visits.</Text>
      </FadeInView>

      <FadeInView delay={40}>
        <View style={styles.segmented}>
          <Pressable
            accessibilityRole="button"
            onPress={() => setTab('favourites')}
            style={[styles.segment, tab === 'favourites' && styles.segmentActive]}
          >
            <Text style={[styles.segmentLabel, tab === 'favourites' && styles.segmentLabelActive]}>
              Favourites
            </Text>
          </Pressable>
          <Pressable
            accessibilityRole="button"
            onPress={() => setTab('history')}
            style={[styles.segment, tab === 'history' && styles.segmentActive]}
          >
            <Text style={[styles.segmentLabel, tab === 'history' && styles.segmentLabelActive]}>
              History
            </Text>
          </Pressable>
        </View>
      </FadeInView>

      {loading ? (
        <FadeInView delay={80} style={styles.loaderWrap}>
          <ActivityIndicator color={theme.colors.accent} size="large" />
        </FadeInView>
      ) : tab === 'favourites' ? (
        favourites.length ? (
          <View style={styles.stack}>
            {favourites.map((item, index) => (
              <FadeInView delay={100 + index * 30} key={item.id}>
                <Card>
                  <View style={styles.cardHeader}>
                    <ProductImage
                      label={item.product_name}
                      uri={item.image_url}
                      variant="thumb"
                    />
                    <View style={styles.cardCopy}>
                      <Text style={styles.title}>{item.product_name}</Text>
                      {!!item.brand && <Text style={styles.brand}>{item.brand}</Text>}
                      <Text style={sharedStyles.footnote}>
                        {item.category || 'Product'}{item.subcategory ? ` / ${item.subcategory}` : ''}
                      </Text>
                      <Text style={sharedStyles.footnote}>Saved {formatDateTime(item.created_at)}</Text>
                    </View>
                  </View>
                  <View style={styles.row}>
                    <PrimaryButton
                      onPress={() =>
                        navigation.navigate('ProductDetail', {
                          barcode: item.barcode,
                          shouldSaveHistory: false,
                        })
                      }
                      style={styles.rowButton}
                    >
                      Open
                    </PrimaryButton>
                    <PrimaryButton
                      onPress={() => handleRemoveFavourite(item)}
                      style={styles.rowButton}
                      variant="quiet"
                    >
                      Remove
                    </PrimaryButton>
                  </View>
                </Card>
              </FadeInView>
            ))}
          </View>
        ) : (
          <FadeInView delay={100}>
            <Card>
              <Text style={styles.title}>No favourites yet</Text>
              <Text style={sharedStyles.body}>Save useful products from the product screen to keep them close.</Text>
            </Card>
          </FadeInView>
        )
      ) : history.length ? (
        <View style={styles.stack}>
          {history.map((item, index) => (
            <FadeInView delay={100 + index * 24} key={item.id}>
              <Card>
                <View style={styles.cardHeader}>
                  <ProductImage
                    label={item.product_name}
                    uri={item.image_url}
                    variant="thumb"
                  />
                  <View style={styles.cardCopy}>
                    <View style={styles.historyTitleRow}>
                      <Text style={styles.title}>{item.product_name}</Text>
                      <StatusPill result={item.safety_result} />
                    </View>
                    {!!item.brand && <Text style={styles.brand}>{item.brand}</Text>}
                    <Text style={sharedStyles.footnote}>{formatDateTime(item.scanned_at)}</Text>
                    {!!item.profile_name && (
                      <Text style={sharedStyles.footnote}>Profile {item.profile_name}</Text>
                    )}
                    <Text style={styles.historySummary}>
                      {sentence(item.allergies, 'No allergy checks')} • {sentence(item.conditions, 'No condition checks')}
                    </Text>
                  </View>
                </View>
                <View style={styles.row}>
                  <PrimaryButton
                    onPress={() =>
                      navigation.navigate('ProductDetail', {
                        barcode: item.barcode,
                        shouldSaveHistory: false,
                      })
                    }
                    style={styles.rowButton}
                  >
                    Open again
                  </PrimaryButton>
                  <PrimaryButton
                    onPress={() => handleDeleteHistory(item)}
                    style={styles.rowButton}
                    variant="quiet"
                  >
                    Delete
                  </PrimaryButton>
                </View>
              </Card>
            </FadeInView>
          ))}
        </View>
      ) : (
        <FadeInView delay={100}>
          <Card>
            <Text style={styles.title}>No scan history yet</Text>
            <Text style={sharedStyles.body}>Successful search and scanner opens will start building your recent checks here.</Text>
          </Card>
        </FadeInView>
      )}
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
      marginBottom: spacing.lg,
    },
    segmented: {
      backgroundColor: theme.colors.surfaceMuted,
      borderRadius: radii.md,
      flexDirection: 'row',
      marginBottom: spacing.lg,
      padding: 4,
    },
    segment: {
      alignItems: 'center',
      borderRadius: radii.sm,
      flex: 1,
      justifyContent: 'center',
      minHeight: 42,
    },
    segmentActive: {
      backgroundColor: theme.colors.surface,
    },
    segmentLabel: {
      color: theme.colors.muted,
      fontSize: 14,
      fontWeight: '700',
      letterSpacing: 0,
    },
    segmentLabelActive: {
      color: theme.colors.accent,
    },
    loaderWrap: {
      alignItems: 'center',
      justifyContent: 'center',
      minHeight: 180,
    },
    stack: {
      gap: spacing.md,
    },
    cardHeader: {
      alignItems: 'flex-start',
      flexDirection: 'row',
      gap: spacing.md,
    },
    cardCopy: {
      flex: 1,
      minHeight: 72,
    },
    historyTitleRow: {
      alignItems: 'flex-start',
      flexDirection: 'row',
      gap: spacing.sm,
      justifyContent: 'space-between',
      marginBottom: spacing.xs,
    },
    title: {
      color: theme.colors.ink,
      fontSize: 18,
      fontWeight: '700',
      lineHeight: 24,
      marginBottom: spacing.xs,
    },
    brand: {
      color: theme.colors.muted,
      fontSize: 13,
      fontWeight: '700',
      lineHeight: 18,
      marginBottom: 2,
    },
    historySummary: {
      color: theme.colors.text,
      fontSize: 14,
      lineHeight: 20,
      marginTop: spacing.xs,
    },
    row: {
      flexDirection: 'row',
      gap: spacing.sm,
      marginTop: spacing.md,
    },
    rowButton: {
      flex: 1,
    },
  });
}
