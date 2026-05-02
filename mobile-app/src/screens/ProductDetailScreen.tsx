import { useEffect, useMemo, useRef, useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  Linking,
  Pressable,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import Card from '../components/Card';
import FadeInView from '../components/FadeInView';
import PrimaryButton from '../components/PrimaryButton';
import ProductImage from '../components/ProductImage';
import Screen from '../components/Screen';
import StatusPill from '../components/StatusPill';
import {
  addCommunityFeedback,
  addFavourite,
  addHistoryEntry,
  deleteFavourite,
  flagCommunityFeedback,
  getCommunityFeedback,
  getFavourites,
  getProductByBarcode,
} from '../api/client';
import { RootScreenProps } from '../navigation/RootNavigator';
import { ALLERGEN_OPTIONS, CONDITION_OPTIONS, useHealthPreferences } from '../state/HealthPreferencesContext';
import {
  CommunityFeedbackItem,
  CommunityFeedbackSummary,
  CommunityFeedbackType,
  ConditionResult,
  Favourite,
  ProductResponse,
} from '../types/api';
import { AppTheme, radii, spacing, useAppTheme } from '../theme';
import { formatDateTime, formatPrice, sentence } from '../utils/format';

type Props = RootScreenProps<'ProductDetail'>;

function toggleValue(values: string[], value: string): string[] {
  return values.includes(value)
    ? values.filter((item) => item !== value)
    : [...values, value];
}

function communityTypeLabel(value: CommunityFeedbackType): string {
  return value === 'positive' ? 'Positive experience' : 'Negative reaction';
}

function optionLabel(value: string, options: { queryValue: string; label: string }[]): string {
  const match = options.find((option) => option.queryValue === value);
  return match?.label ?? value;
}

function formatTagCounts(
  counts: Record<string, number> | undefined,
  options: { queryValue: string; label: string }[],
): string {
  const entries = Object.entries(counts ?? {}).filter(([, count]) => count > 0);
  if (!entries.length) {
    return '';
  }

  return entries
    .map(([key, count]) => `${optionLabel(key, options)} ${count}`)
    .join(' • ');
}

export default function ProductDetailScreen({ route, navigation }: Props) {
  const theme = useAppTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);
  const sharedStyles = theme.sharedStyles;
  const { barcode } = route.params;
  const [product, setProduct] = useState<ProductResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [favourite, setFavourite] = useState<Favourite | null>(null);
  const [favouriteLoading, setFavouriteLoading] = useState(false);
  const [communityLoading, setCommunityLoading] = useState(true);
  const [communitySubmitting, setCommunitySubmitting] = useState(false);
  const [flaggingId, setFlaggingId] = useState<number | null>(null);
  const [communitySummary, setCommunitySummary] = useState<CommunityFeedbackSummary | null>(null);
  const [communityItems, setCommunityItems] = useState<CommunityFeedbackItem[]>([]);
  const [feedbackType, setFeedbackType] = useState<CommunityFeedbackType>('positive');
  const [feedbackComment, setFeedbackComment] = useState('');
  const [feedbackAllergyTags, setFeedbackAllergyTags] = useState<string[]>([]);
  const [feedbackConditionTags, setFeedbackConditionTags] = useState<string[]>([]);
  const {
    activeCount,
    activeProfile,
    activeProfileId,
    selectedAllergens,
    selectedConditions,
  } = useHealthPreferences();
  const historySignatureRef = useRef<string | null>(null);

  useEffect(() => {
    setFeedbackType('positive');
    setFeedbackComment('');
    setFeedbackAllergyTags(selectedAllergens);
    setFeedbackConditionTags(selectedConditions);
  }, [barcode, selectedAllergens, selectedConditions]);

  useEffect(() => {
    let active = true;

    setLoading(true);
    setProduct(null);
    getProductByBarcode(barcode, {
      allergens: selectedAllergens,
      conditions: selectedConditions,
      profileId: activeProfileId,
    })
      .then((data) => {
        if (active) {
          setProduct(data);
        }
      })
      .catch((error) => {
        if (active) {
          Alert.alert('Unable to load product', error instanceof Error ? error.message : 'Check the API.');
        }
      })
      .finally(() => {
        if (active) {
          setLoading(false);
        }
      });

    return () => {
      active = false;
    };
  }, [barcode, selectedAllergens, selectedConditions, activeProfileId]);

  useEffect(() => {
    let active = true;

    getFavourites(barcode)
      .then((items) => {
        if (active) {
          setFavourite(items[0] ?? null);
        }
      })
      .catch(() => {
        if (active) {
          setFavourite(null);
        }
      });

    return () => {
      active = false;
    };
  }, [barcode]);

  useEffect(() => {
    let active = true;

    setCommunityLoading(true);
    getCommunityFeedback(barcode, 20)
      .then((response) => {
        if (active) {
          setCommunitySummary(response.summary);
          setCommunityItems(response.items);
        }
      })
      .catch(() => {
        if (active) {
          setCommunitySummary(null);
          setCommunityItems([]);
        }
      })
      .finally(() => {
        if (active) {
          setCommunityLoading(false);
        }
      });

    return () => {
      active = false;
    };
  }, [barcode]);

  const pricing = product?.pricing ?? product?.pricing_summary ?? {};
  const safetyResult = product?.analysis?.safety_result ?? product?.safety_result;
  const safetyScore = product?.analysis?.safety_score ?? product?.safety_score;
  const reasoning = product?.analysis?.ingredient_reasoning ?? product?.ingredient_reasoning;
  const warnings = product?.analysis?.allergen_warnings ?? product?.allergen_warnings;
  const personalWarnings = product?.analysis?.personal_warnings ?? product?.personal_warnings;
  const personalWarningText = sentence(personalWarnings, '');
  const conditionResultsMap = product?.analysis?.condition_results ?? product?.condition_results ?? {};
  const conditionResults = Object.values(conditionResultsMap ?? {}) as ConditionResult[];
  const bestValueOffer = pricing.best_value_offer;
  const heroImage =
    product?.image_url ||
    pricing.best_offer?.image_url ||
    product?.offers?.find((offer) => !!offer.image_url)?.image_url ||
    null;
  const healthSummary =
    pricing.pricing_summary ||
    (pricing.lowest_in_stock_price != null
      ? `Best live price ${formatPrice(pricing.lowest_in_stock_price)} at ${pricing.cheapest_in_stock_retailer || pricing.cheapest_retailer || 'an available retailer'}.`
      : '');
  const appliedAllergies = product?.requested_allergies ?? selectedAllergens;
  const appliedConditions = product?.requested_conditions ?? selectedConditions;
  const allergyTagSummary = formatTagCounts(communitySummary?.allergy_tag_counts, ALLERGEN_OPTIONS);
  const conditionTagSummary = formatTagCounts(communitySummary?.condition_tag_counts, CONDITION_OPTIONS);
  const canSubmitFeedback = feedbackComment.trim().length >= 4;
  const toneForFeedback = (value: CommunityFeedbackType) =>
    value === 'positive'
      ? { wrapper: styles.positiveBadge, text: styles.positiveBadgeText }
      : { wrapper: styles.negativeBadge, text: styles.negativeBadgeText };

  function triggerSummary(result: ConditionResult): string {
    const triggerNames = (result.triggers ?? [])
      .map((trigger) => trigger.ingredient || trigger.matched_value || trigger.category || trigger.source)
      .filter((value): value is string => Boolean(value && value.trim()));

    return triggerNames.length ? triggerNames.slice(0, 3).join(', ') : '';
  }

  async function refreshCommunity() {
    setCommunityLoading(true);
    try {
      const response = await getCommunityFeedback(barcode, 20);
      setCommunitySummary(response.summary);
      setCommunityItems(response.items);
    } catch (error) {
      setCommunitySummary(null);
      setCommunityItems([]);
    } finally {
      setCommunityLoading(false);
    }
  }

  useEffect(() => {
    if (!product || !route.params.shouldSaveHistory) {
      return;
    }

    const signature = JSON.stringify({
      barcode: product.barcode,
      activeProfileId,
      allergies: appliedAllergies,
      conditions: appliedConditions,
      safetyResult,
      safetyScore,
    });

    if (historySignatureRef.current === signature) {
      return;
    }

    historySignatureRef.current = signature;

    addHistoryEntry({
      barcode: product.barcode,
      product_name: product.name,
      profile_id: activeProfileId,
      profile_name: activeProfile?.name ?? null,
      allergies: appliedAllergies,
      conditions: appliedConditions,
      safety_result: safetyResult ?? null,
      safety_score: safetyScore ?? null,
      condition_results: conditionResultsMap,
    }).catch(() => undefined);
  }, [
    product,
    route.params.shouldSaveHistory,
    activeProfileId,
    activeProfile?.name,
    appliedAllergies,
    appliedConditions,
    safetyResult,
    safetyScore,
    conditionResultsMap,
  ]);

  async function handleFavouritePress() {
    if (!product || favouriteLoading) {
      return;
    }

    try {
      setFavouriteLoading(true);
      if (favourite) {
        await deleteFavourite(favourite.id);
        setFavourite(null);
      } else {
        const created = await addFavourite({
          barcode: product.barcode,
          product_name: product.name,
          profile_id: activeProfileId,
        });
        setFavourite(created);
      }
    } catch (error) {
      Alert.alert('Saved items', 'Unable to update favourites right now.');
    } finally {
      setFavouriteLoading(false);
    }
  }

  async function handleSubmitCommunityFeedback() {
    if (!product || !canSubmitFeedback || communitySubmitting) {
      return;
    }

    try {
      setCommunitySubmitting(true);
      await addCommunityFeedback({
        barcode: product.barcode,
        product_name: product.name,
        feedback_type: feedbackType,
        comment: feedbackComment.trim(),
        allergy_tags: feedbackAllergyTags,
        condition_tags: feedbackConditionTags,
      });
      setFeedbackComment('');
      await refreshCommunity();
    } catch (error) {
      Alert.alert('Community experiences', 'Unable to save your feedback right now.');
    } finally {
      setCommunitySubmitting(false);
    }
  }

  async function handleFlagFeedback(item: CommunityFeedbackItem) {
    try {
      setFlaggingId(item.id);
      await flagCommunityFeedback(item.id, 'Reported from the mobile app');
      await refreshCommunity();
      Alert.alert('Community experiences', 'Thanks. This feedback has been flagged for review.');
    } catch (error) {
      Alert.alert('Community experiences', 'Unable to report this feedback right now.');
    } finally {
      setFlaggingId(null);
    }
  }

  if (loading) {
    return (
      <Screen>
        <View style={styles.centered}>
          <ActivityIndicator color={theme.colors.accent} size="large" />
        </View>
      </Screen>
    );
  }

  if (!product) {
    return (
      <Screen>
        <Text style={sharedStyles.screenTitle}>Product not found</Text>
      </Screen>
    );
  }

  return (
    <Screen>
      <FadeInView>
        <Card style={styles.heroCard}>
          <ProductImage label={product.name} uri={heroImage} variant="hero" />
          <View style={styles.heroCopy}>
            <View style={styles.topLine}>
              <Text style={styles.brand}>{product.brand || 'SafeBite'}</Text>
              {activeCount > 0 ? <Text style={styles.healthBadge}>{activeCount} health</Text> : null}
            </View>
            <Text style={sharedStyles.screenTitle}>{product.name}</Text>
            <Text style={styles.meta}>
              {product.category || 'Uncategorised'} / {product.subcategory || 'General'}
            </Text>
            {!!activeProfile && <Text style={styles.profileLine}>Profile {activeProfile.name}</Text>}
          </View>
        </Card>
      </FadeInView>

      <FadeInView delay={35}>
        <Card style={styles.card}>
        <View style={styles.resultHeader}>
          <Text style={sharedStyles.sectionTitle}>Safety</Text>
          <StatusPill result={safetyResult} />
        </View>
        <Text style={styles.score}>{safetyScore ?? 'N/A'}</Text>
        <Text style={sharedStyles.body}>{sentence(reasoning, 'No reasoning available yet.')}</Text>
        <Text style={styles.warning}>{sentence(warnings, 'No allergen warnings returned.')}</Text>
        {!!personalWarningText && <Text style={styles.personalWarning}>{personalWarningText}</Text>}
        </Card>
      </FadeInView>

      {activeCount > 0 && (
        <FadeInView delay={60}>
          <Card style={styles.card}>
          <Text style={sharedStyles.sectionTitle}>Health checks</Text>
          <Text style={sharedStyles.footnote}>
            These results stay separate from the core safety score.
          </Text>

          {conditionResults.length > 0 ? (
            <View style={styles.healthStack}>
              {conditionResults.map((result) => {
                const triggerText = triggerSummary(result);
                const suggestionText = sentence(result.suggestions, '');

                return (
                  <View key={result.condition} style={styles.healthResult}>
                    <View style={styles.healthResultHeader}>
                      <View style={styles.healthResultCopy}>
                        <Text style={styles.healthResultTitle}>{result.display_name}</Text>
                        <Text style={sharedStyles.footnote}>
                          {result.kind === 'allergy' ? 'Allergy check' : 'Condition check'}
                        </Text>
                      </View>
                      <StatusPill result={result.result} />
                    </View>

                    {!!result.summary && <Text style={sharedStyles.body}>{result.summary}</Text>}
                    {!!result.explanation && result.explanation !== result.summary && (
                      <Text style={styles.healthExplanation}>{result.explanation}</Text>
                    )}
                    {!!triggerText && <Text style={styles.healthTrigger}>Triggers: {triggerText}</Text>}
                    {!!suggestionText && (
                      <Text style={styles.healthSuggestion}>Next step: {suggestionText}</Text>
                    )}
                  </View>
                );
              })}
            </View>
          ) : (
            <Text style={sharedStyles.body}>No condition results were returned for the current health checks.</Text>
          )}
          </Card>
        </FadeInView>
      )}

      <FadeInView delay={90}>
        <Card style={styles.card}>
        <Text style={sharedStyles.sectionTitle}>Best price</Text>
        <Text style={styles.price}>{formatPrice(pricing.best_price)}</Text>
        <Text style={sharedStyles.body}>{pricing.cheapest_retailer || 'Retailer unavailable'}</Text>
        <Text style={sharedStyles.footnote}>{pricing.stock_status || 'Stock status unavailable'}</Text>
        {!!healthSummary && <Text style={styles.pricingSummary}>{healthSummary}</Text>}
        <View style={styles.pricingMetaWrap}>
          {pricing.lowest_standard_price != null && (
            <Text style={styles.pricingMeta}>Standard from {formatPrice(pricing.lowest_standard_price)}</Text>
          )}
          {pricing.lowest_promo_price != null && (
            <Text style={styles.pricingMeta}>Promo from {formatPrice(pricing.lowest_promo_price)}</Text>
          )}
          {pricing.promo_offer_count ? (
            <Text style={styles.pricingMeta}>{pricing.promo_offer_count} promo offer{pricing.promo_offer_count === 1 ? '' : 's'}</Text>
          ) : null}
          {pricing.multi_buy_offer_count ? (
            <Text style={styles.pricingMeta}>{pricing.multi_buy_offer_count} multi-buy option{pricing.multi_buy_offer_count === 1 ? '' : 's'}</Text>
          ) : null}
        </View>
        {pricing.best_value_price != null && (
          <View style={styles.valueCard}>
            <Text style={styles.valueTitle}>Best value</Text>
            <Text style={styles.valuePrice}>{formatPrice(pricing.best_value_price)}</Text>
            <Text style={sharedStyles.body}>
              {pricing.best_value_retailer || bestValueOffer?.retailer || 'Retailer unavailable'}
            </Text>
            {!!bestValueOffer?.promotion_label && (
              <Text style={styles.valueBadge}>{bestValueOffer.promotion_label}</Text>
            )}
            {!!bestValueOffer?.promotion_summary && (
              <Text style={styles.valueSummary}>{bestValueOffer.promotion_summary}</Text>
            )}
          </View>
        )}
        {!!pricing.product_url && (
          <PrimaryButton
            onPress={() => Linking.openURL(pricing.product_url || '')}
            style={styles.retailerButton}
            variant="secondary"
          >
            Open retailer
          </PrimaryButton>
        )}
        </Card>
      </FadeInView>

      <FadeInView delay={120}>
        <Card style={styles.card}>
        <Text style={sharedStyles.sectionTitle}>Ingredients</Text>
        <Text style={sharedStyles.body}>{sentence(product.ingredients, 'No ingredients available yet.')}</Text>
        </Card>
      </FadeInView>

      <FadeInView delay={145}>
        <Card style={styles.card}>
        <Text style={sharedStyles.sectionTitle}>Allergens</Text>
        <Text style={sharedStyles.body}>{sentence(product.allergens, 'No allergens listed.')}</Text>
        </Card>
      </FadeInView>

      <FadeInView delay={170}>
        <Card style={styles.card}>
        <View style={styles.resultHeader}>
          <Text style={sharedStyles.sectionTitle}>Community experiences</Text>
          <Text style={styles.feedbackCount}>
            {communitySummary?.visible_count ?? communityItems.length} posts
          </Text>
        </View>
        <Text style={styles.communityDisclaimer}>
          {communitySummary?.disclaimer || 'Reported by users only. This does not change the verified safety analysis.'}
        </Text>

        {!!communitySummary && (
          <View style={styles.communitySummaryWrap}>
            <View style={styles.summaryPills}>
              <View style={[styles.summaryPill, styles.positiveBadge]}>
                <Text style={[styles.summaryPillText, styles.positiveBadgeText]}>
                  {communitySummary.positive_count} positive
                </Text>
              </View>
              <View style={[styles.summaryPill, styles.negativeBadge]}>
                <Text style={[styles.summaryPillText, styles.negativeBadgeText]}>
                  {communitySummary.negative_count} negative
                </Text>
              </View>
            </View>
            {!!allergyTagSummary && (
              <Text style={sharedStyles.footnote}>Allergy tags: {allergyTagSummary}</Text>
            )}
            {!!conditionTagSummary && (
              <Text style={sharedStyles.footnote}>Condition tags: {conditionTagSummary}</Text>
            )}
          </View>
        )}

        <View style={styles.feedbackComposer}>
          <Text style={styles.feedbackSectionTitle}>Share your experience</Text>
          <Text style={sharedStyles.footnote}>
            Keep it short and factual. This section is user opinion, not verified medical guidance.
          </Text>

          <View style={styles.feedbackTypeRow}>
            {(['positive', 'negative'] as CommunityFeedbackType[]).map((value) => {
              const selected = feedbackType === value;
              const tone = toneForFeedback(value);
              return (
                <Pressable
                  key={value}
                  accessibilityRole="button"
                  onPress={() => setFeedbackType(value)}
                  style={[
                    styles.feedbackTypeButton,
                    selected ? tone.wrapper : styles.feedbackTypeIdle,
                  ]}
                >
                  <Text
                    style={[
                      styles.feedbackTypeButtonText,
                      selected ? tone.text : styles.feedbackTypeIdleText,
                    ]}
                  >
                    {communityTypeLabel(value)}
                  </Text>
                </Pressable>
              );
            })}
          </View>

          <TextInput
            maxLength={280}
            multiline
            onChangeText={setFeedbackComment}
            placeholder="Share what happened for you."
            placeholderTextColor={theme.colors.muted}
            style={styles.feedbackInput}
            textAlignVertical="top"
            value={feedbackComment}
          />
          <Text style={styles.characterCount}>{feedbackComment.trim().length}/280</Text>

          <Text style={styles.feedbackLabel}>Allergy tags</Text>
          <View style={styles.tagWrap}>
            {ALLERGEN_OPTIONS.map((option) => {
              const selected = feedbackAllergyTags.includes(option.queryValue);
              return (
                <Pressable
                  key={option.key}
                  accessibilityRole="button"
                  onPress={() => setFeedbackAllergyTags((current) => toggleValue(current, option.queryValue))}
                  style={[styles.tagButton, selected && styles.tagButtonSelected]}
                >
                  <Text style={[styles.tagButtonText, selected && styles.tagButtonTextSelected]}>
                    {option.label}
                  </Text>
                </Pressable>
              );
            })}
          </View>

          <Text style={styles.feedbackLabel}>Condition tags</Text>
          <View style={styles.tagWrap}>
            {CONDITION_OPTIONS.map((option) => {
              const selected = feedbackConditionTags.includes(option.queryValue);
              return (
                <Pressable
                  key={option.key}
                  accessibilityRole="button"
                  onPress={() => setFeedbackConditionTags((current) => toggleValue(current, option.queryValue))}
                  style={[styles.tagButton, selected && styles.tagButtonSelected]}
                >
                  <Text style={[styles.tagButtonText, selected && styles.tagButtonTextSelected]}>
                    {option.label}
                  </Text>
                </Pressable>
              );
            })}
          </View>

          <PrimaryButton
            disabled={!canSubmitFeedback}
            loading={communitySubmitting}
            onPress={handleSubmitCommunityFeedback}
            style={styles.communityButton}
          >
            Submit experience
          </PrimaryButton>
        </View>

        <View style={styles.feedbackFeed}>
          <Text style={styles.feedbackSectionTitle}>Recent experiences</Text>
          {communityLoading ? (
            <View style={styles.communityLoader}>
              <ActivityIndicator color={theme.colors.accent} size="small" />
            </View>
          ) : communityItems.length ? (
            communityItems.map((item) => {
              const tone = toneForFeedback(item.feedback_type);
              const tagParts = [
                ...(item.allergy_tags ?? []).map((tag) => optionLabel(tag, ALLERGEN_OPTIONS)),
                ...(item.condition_tags ?? []).map((tag) => optionLabel(tag, CONDITION_OPTIONS)),
              ];
              return (
                <View key={item.id} style={styles.feedbackItem}>
                  <View style={styles.feedbackItemHeader}>
                    <View style={styles.feedbackItemCopy}>
                      <View style={[styles.summaryPill, tone.wrapper]}>
                        <Text style={[styles.summaryPillText, tone.text]}>
                          {communityTypeLabel(item.feedback_type)}
                        </Text>
                      </View>
                      <Text style={sharedStyles.footnote}>{formatDateTime(item.created_at)}</Text>
                    </View>
                    <Pressable
                      accessibilityRole="button"
                      disabled={flaggingId === item.id}
                      onPress={() => handleFlagFeedback(item)}
                      style={styles.flagButton}
                    >
                      <Text style={styles.flagButtonText}>
                        {flaggingId === item.id ? 'Reporting…' : 'Report'}
                      </Text>
                    </Pressable>
                  </View>
                  <Text style={sharedStyles.body}>{item.comment}</Text>
                  {!!tagParts.length && (
                    <Text style={styles.feedbackTags}>Tags: {tagParts.join(', ')}</Text>
                  )}
                  <Text style={styles.feedbackOpinionLine}>User experience only</Text>
                </View>
              );
            })
          ) : (
            <Text style={sharedStyles.body}>
              No community feedback yet. Be the first to share a short experience.
            </Text>
          )}
        </View>
        </Card>
      </FadeInView>

      <FadeInView delay={205}>
        <View style={styles.actionStack}>
          <PrimaryButton
            onPress={() => navigation.navigate('Alternatives', { barcode: product.barcode, name: product.name })}
          >
            View alternatives
          </PrimaryButton>
          <PrimaryButton
            loading={favouriteLoading}
            onPress={handleFavouritePress}
            style={styles.favouriteButton}
            variant={favourite ? 'secondary' : 'quiet'}
          >
            {favourite ? 'Remove favourite' : 'Save favourite'}
          </PrimaryButton>
        </View>
      </FadeInView>
    </Screen>
  );
}

function createStyles(theme: AppTheme) {
  return StyleSheet.create({
    centered: {
      alignItems: 'center',
      flex: 1,
      justifyContent: 'center',
    },
    heroCard: {
      marginBottom: spacing.md,
      overflow: 'hidden',
      padding: spacing.md,
    },
    heroCopy: {
      paddingTop: spacing.md,
    },
    topLine: {
      alignItems: 'center',
      flexDirection: 'row',
      justifyContent: 'space-between',
      marginBottom: spacing.sm,
    },
    brand: {
      color: theme.colors.accent,
      fontSize: 14,
      fontWeight: '800',
      letterSpacing: 0,
      textTransform: 'uppercase',
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
    meta: {
      color: theme.colors.muted,
      fontSize: 15,
      lineHeight: 21,
      marginTop: spacing.sm,
    },
    profileLine: {
      color: theme.colors.blue,
      fontSize: 14,
      fontWeight: '600',
      lineHeight: 20,
      marginTop: spacing.sm,
    },
    card: {
      marginBottom: spacing.md,
    },
    healthStack: {
      gap: spacing.md,
      marginTop: spacing.md,
    },
    healthResult: {
      borderColor: theme.colors.border,
      borderTopWidth: StyleSheet.hairlineWidth,
      paddingTop: spacing.md,
    },
    healthResultHeader: {
      alignItems: 'flex-start',
      flexDirection: 'row',
      gap: spacing.md,
      justifyContent: 'space-between',
      marginBottom: spacing.sm,
    },
    healthResultCopy: {
      flex: 1,
    },
    healthResultTitle: {
      color: theme.colors.ink,
      fontSize: 16,
      fontWeight: '700',
      lineHeight: 22,
      marginBottom: 4,
    },
    healthExplanation: {
      color: theme.colors.text,
      fontSize: 14,
      lineHeight: 20,
      marginTop: spacing.xs,
    },
    healthTrigger: {
      color: theme.colors.caution,
      fontSize: 14,
      fontWeight: '600',
      lineHeight: 20,
      marginTop: spacing.xs,
    },
    healthSuggestion: {
      color: theme.colors.blue,
      fontSize: 14,
      fontWeight: '600',
      lineHeight: 20,
      marginTop: spacing.xs,
    },
    resultHeader: {
      alignItems: 'flex-start',
      flexDirection: 'row',
      justifyContent: 'space-between',
      marginBottom: spacing.md,
    },
    score: {
      color: theme.colors.ink,
      fontSize: 42,
      fontWeight: '800',
      lineHeight: 48,
      marginBottom: spacing.sm,
    },
    warning: {
      color: theme.colors.caution,
      fontSize: 14,
      fontWeight: '600',
      lineHeight: 20,
      marginTop: spacing.sm,
    },
    personalWarning: {
      color: theme.colors.avoid,
      fontSize: 14,
      fontWeight: '600',
      lineHeight: 20,
      marginTop: spacing.sm,
    },
    price: {
      color: theme.colors.ink,
      fontSize: 34,
      fontWeight: '800',
      lineHeight: 38,
      marginVertical: spacing.sm,
    },
    pricingSummary: {
      color: theme.colors.text,
      fontSize: 14,
      lineHeight: 20,
      marginTop: spacing.sm,
    },
    pricingMetaWrap: {
      gap: spacing.xs,
      marginTop: spacing.md,
    },
    pricingMeta: {
      color: theme.colors.muted,
      fontSize: 13,
      fontWeight: '600',
      lineHeight: 18,
    },
    valueCard: {
      backgroundColor: theme.colors.surfaceMuted,
      borderColor: theme.colors.border,
      borderRadius: radii.md,
      borderWidth: 1,
      marginTop: spacing.md,
      padding: spacing.md,
    },
    valueTitle: {
      color: theme.colors.blue,
      fontSize: 13,
      fontWeight: '800',
      lineHeight: 18,
      marginBottom: spacing.xs,
      textTransform: 'uppercase',
    },
    valuePrice: {
      color: theme.colors.ink,
      fontSize: 24,
      fontWeight: '800',
      lineHeight: 28,
      marginBottom: spacing.xs,
    },
    valueBadge: {
      color: theme.colors.accent,
      fontSize: 13,
      fontWeight: '700',
      lineHeight: 18,
      marginTop: spacing.sm,
    },
    valueSummary: {
      color: theme.colors.text,
      fontSize: 13,
      lineHeight: 18,
      marginTop: spacing.xs,
    },
    retailerButton: {
      marginTop: spacing.md,
    },
    feedbackCount: {
      color: theme.colors.accent,
      fontSize: 13,
      fontWeight: '700',
      lineHeight: 18,
    },
    communityDisclaimer: {
      color: theme.colors.blue,
      fontSize: 14,
      fontWeight: '600',
      lineHeight: 20,
    },
    communitySummaryWrap: {
      marginTop: spacing.md,
    },
    summaryPills: {
      flexDirection: 'row',
      flexWrap: 'wrap',
      gap: spacing.sm,
      marginBottom: spacing.sm,
    },
    summaryPill: {
      alignSelf: 'flex-start',
      borderRadius: radii.pill,
      paddingHorizontal: 10,
      paddingVertical: 6,
    },
    summaryPillText: {
      fontSize: 13,
      fontWeight: '700',
    },
    positiveBadge: {
      backgroundColor: theme.colors.safeSurface,
    },
    positiveBadgeText: {
      color: theme.colors.safe,
    },
    negativeBadge: {
      backgroundColor: theme.colors.avoidSurface,
    },
    negativeBadgeText: {
      color: theme.colors.avoid,
    },
    feedbackComposer: {
      borderColor: theme.colors.border,
      borderTopWidth: StyleSheet.hairlineWidth,
      marginTop: spacing.lg,
      paddingTop: spacing.lg,
    },
    feedbackFeed: {
      borderColor: theme.colors.border,
      borderTopWidth: StyleSheet.hairlineWidth,
      marginTop: spacing.lg,
      paddingTop: spacing.lg,
    },
    feedbackSectionTitle: {
      color: theme.colors.ink,
      fontSize: 17,
      fontWeight: '700',
      lineHeight: 22,
      marginBottom: spacing.sm,
    },
    feedbackTypeRow: {
      flexDirection: 'row',
      gap: spacing.sm,
      marginBottom: spacing.md,
      marginTop: spacing.md,
    },
    feedbackTypeButton: {
      alignItems: 'center',
      borderRadius: radii.md,
      borderWidth: 1,
      flex: 1,
      justifyContent: 'center',
      minHeight: 44,
      paddingHorizontal: 10,
      paddingVertical: 10,
    },
    feedbackTypeIdle: {
      backgroundColor: theme.colors.surfaceMuted,
      borderColor: theme.colors.border,
    },
    feedbackTypeButtonText: {
      fontSize: 14,
      fontWeight: '700',
      textAlign: 'center',
    },
    feedbackTypeIdleText: {
      color: theme.colors.text,
    },
    feedbackInput: {
      backgroundColor: theme.colors.inputBackground,
      borderColor: theme.colors.border,
      borderRadius: radii.md,
      borderWidth: 1,
      color: theme.colors.ink,
      fontSize: 15,
      lineHeight: 21,
      marginTop: spacing.sm,
      minHeight: 110,
      padding: 14,
    },
    characterCount: {
      color: theme.colors.muted,
      fontSize: 12,
      fontWeight: '600',
      marginTop: spacing.xs,
      textAlign: 'right',
    },
    feedbackLabel: {
      color: theme.colors.text,
      fontSize: 14,
      fontWeight: '700',
      marginBottom: spacing.sm,
      marginTop: spacing.md,
    },
    tagWrap: {
      flexDirection: 'row',
      flexWrap: 'wrap',
      gap: spacing.sm,
    },
    tagButton: {
      backgroundColor: theme.colors.surface,
      borderColor: theme.colors.border,
      borderRadius: radii.sm,
      borderWidth: 1,
      justifyContent: 'center',
      minHeight: 36,
      paddingHorizontal: 12,
      paddingVertical: 8,
    },
    tagButtonSelected: {
      backgroundColor: theme.colors.accentSoft,
      borderColor: theme.colors.accent,
    },
    tagButtonText: {
      color: theme.colors.text,
      fontSize: 13,
      fontWeight: '700',
    },
    tagButtonTextSelected: {
      color: theme.colors.accent,
    },
    communityButton: {
      marginTop: spacing.lg,
    },
    communityLoader: {
      alignItems: 'center',
      justifyContent: 'center',
      minHeight: 80,
    },
    feedbackItem: {
      borderColor: theme.colors.border,
      borderTopWidth: StyleSheet.hairlineWidth,
      marginTop: spacing.md,
      paddingTop: spacing.md,
    },
    feedbackItemHeader: {
      alignItems: 'flex-start',
      flexDirection: 'row',
      gap: spacing.md,
      justifyContent: 'space-between',
      marginBottom: spacing.sm,
    },
    feedbackItemCopy: {
      flex: 1,
      gap: spacing.xs,
    },
    feedbackTags: {
      color: theme.colors.caution,
      fontSize: 13,
      fontWeight: '600',
      lineHeight: 18,
      marginTop: spacing.sm,
    },
    feedbackOpinionLine: {
      color: theme.colors.muted,
      fontSize: 12,
      fontWeight: '700',
      lineHeight: 16,
      marginTop: spacing.sm,
      textTransform: 'uppercase',
    },
    flagButton: {
      paddingHorizontal: 2,
      paddingVertical: 4,
    },
    flagButtonText: {
      color: theme.colors.blue,
      fontSize: 13,
      fontWeight: '700',
    },
    actionStack: {
      gap: spacing.sm,
      marginBottom: spacing.lg,
    },
    favouriteButton: {
      marginTop: 0,
    },
  });
}
