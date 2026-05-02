import { useMemo, useState } from 'react';
import { Alert, Pressable, StyleSheet, Text, TextInput, View } from 'react-native';
import Card from '../components/Card';
import FadeInView from '../components/FadeInView';
import PrimaryButton from '../components/PrimaryButton';
import ProductCard from '../components/ProductCard';
import Screen from '../components/Screen';
import { applyPromoCode, validatePromoCode } from '../api/client';
import { ProductSummary, PromoCodeApplyResult, PromoCodeValidationResult } from '../types/api';
import { MainTabScreenProps } from '../navigation/RootNavigator';
import { useHealthPreferences } from '../state/HealthPreferencesContext';
import { formatPrice } from '../utils/format';
import { AppTheme, radii, spacing, useAppTheme } from '../theme';

type Props = MainTabScreenProps<'Home'>;
type AccessPlan = 'monthly' | 'annual';

const demoProduct: ProductSummary = {
  barcode: '5056000505910',
  name: 'Kendamil Classic First Infant Milk Stage 1 800g',
  brand: 'Kendamil',
  category: 'Baby & Toddler',
  subcategory: 'Formula Milk',
  safety_result: 'Caution',
  safety_score: 55,
  best_price: 11.35,
  cheapest_retailer: "Sainsbury's",
};

const latestFruitPuree: ProductSummary = {
  barcode: '5060107330214',
  name: "Ella's Kitchen Apples Carrots Plus Parsnips 120G",
  brand: "Ella's Kitchen",
  category: 'Baby & Toddler',
  subcategory: 'Fruit Puree',
  safety_result: 'Caution',
  safety_score: 78,
  best_price: 1.2,
  cheapest_retailer: 'Tesco',
};

function promoSummaryText(
  result: PromoCodeValidationResult | PromoCodeApplyResult | null,
): string {
  const preview = result?.preview;
  if (!preview) {
    return '';
  }

  if (preview.trial_extension_days) {
    return `${preview.trial_extension_days} extra trial days on the ${preview.plan} plan.`;
  }

  const pieces = [
    `Base ${formatPrice(preview.base_price)}`,
    `final ${formatPrice(preview.final_price)}`,
  ];

  if (typeof preview.discount_amount === 'number' && preview.discount_amount > 0) {
    pieces.push(`save ${formatPrice(preview.discount_amount)}`);
  }

  return pieces.join(' • ');
}

export default function HomeScreen({ navigation }: Props) {
  const theme = useAppTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);
  const sharedStyles = theme.sharedStyles;
  const { activeCount, activeProfile } = useHealthPreferences();
  const [promoCode, setPromoCode] = useState('');
  const [plan, setPlan] = useState<AccessPlan>('monthly');
  const [promoValidation, setPromoValidation] = useState<PromoCodeValidationResult | null>(null);
  const [promoApplied, setPromoApplied] = useState<PromoCodeApplyResult | null>(null);
  const [validatingPromo, setValidatingPromo] = useState(false);
  const [applyingPromo, setApplyingPromo] = useState(false);

  const trimmedPromoCode = promoCode.trim().toUpperCase();
  const hasPromoCode = trimmedPromoCode.length > 0;
  const promoPreview = promoApplied?.preview ?? promoValidation?.preview ?? null;
  const promoNotice =
    promoApplied?.pricing_separation_notice ??
    promoValidation?.pricing_separation_notice ??
    'Promo codes change access pricing only. They do not change product safety.';

  async function handleValidatePromo() {
    if (!hasPromoCode) {
      Alert.alert('Promo code', 'Enter a code to check it.');
      return;
    }

    try {
      setValidatingPromo(true);
      setPromoApplied(null);
      const result = await validatePromoCode({ code: trimmedPromoCode, plan });
      setPromoValidation(result);
      if (!result.valid) {
        Alert.alert('Promo code', result.reason || 'That code is not available right now.');
      }
    } catch {
      Alert.alert('Promo code', 'Unable to validate this code right now.');
    } finally {
      setValidatingPromo(false);
    }
  }

  async function handleApplyPromo() {
    if (!hasPromoCode) {
      Alert.alert('Promo code', 'Enter a code to apply it.');
      return;
    }

    try {
      setApplyingPromo(true);
      const result = await applyPromoCode({ code: trimmedPromoCode, plan });
      setPromoApplied(result);
      setPromoValidation(null);
      if (!result.applied) {
        Alert.alert('Promo code', result.reason || 'That code could not be applied.');
        return;
      }

      Alert.alert(
        'Promo applied',
        promoSummaryText(result) || 'Your access pricing preview has been updated.',
      );
    } catch {
      Alert.alert('Promo code', 'Unable to apply this code right now.');
    } finally {
      setApplyingPromo(false);
    }
  }

  return (
    <Screen>
      <FadeInView>
        <View style={styles.header}>
          <Text style={styles.brand}>SafeBite</Text>
          <Text style={sharedStyles.screenTitle}>Calm product checks with premium clarity.</Text>
          <Text style={styles.subtitle}>
            Scan, search, compare, and review health notes without losing the fast read on price and safety.
          </Text>
        </View>
      </FadeInView>

      <FadeInView delay={40}>
        <Card style={styles.heroCard}>
          <View style={styles.quickHeader}>
            <View style={styles.heroCopy}>
              <Text style={sharedStyles.sectionTitle}>Quick start</Text>
              <Text style={styles.helperCopy}>
                {activeProfile
                  ? `Ready with ${activeProfile.name}.`
                  : 'Start with a scan or search, then save the setup you use most.'}
              </Text>
            </View>
            {activeCount > 0 ? <Text style={styles.healthBadge}>{activeCount} active</Text> : null}
          </View>

          <View style={styles.buttonRow}>
            <PrimaryButton
              onPress={() => navigation.navigate('Scanner')}
              style={styles.rowButton}
            >
              Scan now
            </PrimaryButton>
            <PrimaryButton
              onPress={() => navigation.navigate('Search')}
              style={styles.rowButton}
              variant="secondary"
            >
              Search
            </PrimaryButton>
          </View>

          <PrimaryButton
            onPress={() => navigation.navigate('Health')}
            style={styles.healthButton}
            variant="quiet"
          >
            Review health checks
          </PrimaryButton>
        </Card>
      </FadeInView>

      <FadeInView delay={80}>
        <Card style={styles.heroCard}>
          <View style={styles.promoHeader}>
            <View style={styles.heroCopy}>
              <Text style={sharedStyles.sectionTitle}>Access promo codes</Text>
              <Text style={styles.helperCopy}>
                Codes affect access pricing only, never the product verdict.
              </Text>
            </View>
            <Text style={styles.scopePill}>Phase 7</Text>
          </View>

          <View style={styles.planRow}>
            {(['monthly', 'annual'] as AccessPlan[]).map((value) => {
              const selected = plan === value;
              return (
                <Pressable
                  key={value}
                  accessibilityRole="button"
                  onPress={() => setPlan(value)}
                  style={[styles.planButton, selected && styles.planButtonSelected]}
                >
                  <Text style={[styles.planButtonText, selected && styles.planButtonTextSelected]}>
                    {value === 'monthly' ? 'Monthly' : 'Annual'}
                  </Text>
                </Pressable>
              );
            })}
          </View>

          <TextInput
            autoCapitalize="characters"
            autoCorrect={false}
            onChangeText={(value) => setPromoCode(value.toUpperCase())}
            placeholder="Enter promo code"
            placeholderTextColor={theme.colors.muted}
            style={styles.promoInput}
            value={promoCode}
          />

          <View style={styles.buttonRow}>
            <PrimaryButton
              disabled={!hasPromoCode}
              loading={validatingPromo}
              onPress={handleValidatePromo}
              style={styles.rowButton}
              variant="secondary"
            >
              Check code
            </PrimaryButton>
            <PrimaryButton
              disabled={!hasPromoCode}
              loading={applyingPromo}
              onPress={handleApplyPromo}
              style={styles.rowButton}
            >
              Apply code
            </PrimaryButton>
          </View>

          {promoPreview ? (
            <View style={styles.promoPreview}>
              <Text style={styles.promoPreviewTitle}>
                {promoPreview.campaign_label || promoPreview.code_type || 'Promo preview'}
              </Text>
              <Text style={styles.promoPriceLine}>{promoSummaryText(promoApplied ?? promoValidation)}</Text>
              {promoPreview.savings_percent && promoPreview.savings_percent > 0 ? (
                <Text style={styles.promoMeta}>
                  Savings {promoPreview.savings_percent.toFixed(0)}%
                </Text>
              ) : null}
              {promoPreview.expires_at ? (
                <Text style={styles.promoMeta}>Expires {promoPreview.expires_at}</Text>
              ) : null}
              <Text style={styles.promoNotice}>{promoNotice}</Text>
            </View>
          ) : null}
        </Card>
      </FadeInView>

      <FadeInView delay={120}>
        <View style={styles.sectionHeader}>
          <Text style={sharedStyles.sectionTitle}>Featured live checks</Text>
          <Text style={styles.sectionFootnote}>Fresh data from the current catalog</Text>
        </View>
      </FadeInView>

      <FadeInView delay={150}>
        <ProductCard
          label="Formula milk"
          product={demoProduct}
          onPress={() =>
            navigation.navigate('ProductDetail', {
              barcode: demoProduct.barcode,
              shouldSaveHistory: false,
            })
          }
        />
      </FadeInView>

      <FadeInView delay={190}>
        <ProductCard
          label="Latest verified fruit puree"
          product={latestFruitPuree}
          onPress={() =>
            navigation.navigate('ProductDetail', {
              barcode: latestFruitPuree.barcode,
              shouldSaveHistory: false,
            })
          }
        />
      </FadeInView>
    </Screen>
  );
}

function createStyles(theme: AppTheme) {
  return StyleSheet.create({
    header: {
      marginBottom: spacing.lg,
      paddingTop: spacing.sm,
    },
    brand: {
      color: theme.colors.accent,
      fontSize: 14,
      fontWeight: '800',
      letterSpacing: 0,
      marginBottom: spacing.sm,
      textTransform: 'uppercase',
    },
    subtitle: {
      color: theme.colors.muted,
      fontSize: 16,
      lineHeight: 23,
      marginTop: spacing.sm,
      maxWidth: 520,
    },
    heroCard: {
      marginBottom: spacing.md,
    },
    quickHeader: {
      alignItems: 'flex-start',
      flexDirection: 'row',
      gap: spacing.md,
      justifyContent: 'space-between',
      marginBottom: spacing.md,
    },
    heroCopy: {
      flex: 1,
    },
    helperCopy: {
      color: theme.colors.muted,
      fontSize: 14,
      lineHeight: 20,
      marginTop: spacing.xs,
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
    buttonRow: {
      flexDirection: 'row',
      gap: spacing.sm,
    },
    rowButton: {
      flex: 1,
    },
    healthButton: {
      marginTop: spacing.sm,
    },
    promoHeader: {
      alignItems: 'flex-start',
      flexDirection: 'row',
      gap: spacing.md,
      justifyContent: 'space-between',
      marginBottom: spacing.md,
    },
    scopePill: {
      backgroundColor: theme.colors.surfaceMuted,
      borderRadius: radii.pill,
      color: theme.colors.ink,
      fontSize: 12,
      fontWeight: '700',
      overflow: 'hidden',
      paddingHorizontal: 12,
      paddingVertical: 7,
    },
    planRow: {
      backgroundColor: theme.colors.surfaceMuted,
      borderRadius: radii.md,
      flexDirection: 'row',
      marginBottom: spacing.md,
      padding: 4,
    },
    planButton: {
      alignItems: 'center',
      borderRadius: radii.sm,
      flex: 1,
      justifyContent: 'center',
      minHeight: 42,
    },
    planButtonSelected: {
      backgroundColor: theme.colors.surface,
    },
    planButtonText: {
      color: theme.colors.muted,
      fontSize: 14,
      fontWeight: '700',
      letterSpacing: 0,
    },
    planButtonTextSelected: {
      color: theme.colors.accent,
    },
    promoInput: {
      backgroundColor: theme.colors.inputBackground,
      borderColor: theme.colors.border,
      borderRadius: radii.md,
      borderWidth: 1,
      color: theme.colors.ink,
      fontSize: 16,
      marginBottom: spacing.md,
      minHeight: 52,
      paddingHorizontal: 16,
    },
    promoPreview: {
      backgroundColor: theme.colors.surfaceMuted,
      borderRadius: radii.md,
      marginTop: spacing.md,
      padding: spacing.md,
    },
    promoPreviewTitle: {
      color: theme.colors.ink,
      fontSize: 16,
      fontWeight: '700',
      lineHeight: 20,
      marginBottom: spacing.xs,
    },
    promoPriceLine: {
      color: theme.colors.text,
      fontSize: 14,
      fontWeight: '600',
      lineHeight: 20,
    },
    promoMeta: {
      color: theme.colors.muted,
      fontSize: 12,
      fontWeight: '700',
      marginTop: spacing.xs,
    },
    promoNotice: {
      color: theme.colors.muted,
      fontSize: 12,
      lineHeight: 18,
      marginTop: spacing.sm,
    },
    sectionHeader: {
      alignItems: 'flex-end',
      flexDirection: 'row',
      justifyContent: 'space-between',
      marginTop: spacing.sm,
      marginBottom: spacing.md,
    },
    sectionFootnote: {
      color: theme.colors.muted,
      fontSize: 12,
      fontWeight: '600',
      lineHeight: 16,
      textAlign: 'right',
    },
  });
}
