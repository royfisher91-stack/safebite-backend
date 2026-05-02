import { PropsWithChildren, useMemo } from 'react';
import { ActivityIndicator, Pressable, StyleProp, StyleSheet, Text, ViewStyle } from 'react-native';
import { radii, spacing, useAppTheme } from '../theme';

type Props = PropsWithChildren<{
  onPress: () => void;
  variant?: 'primary' | 'secondary' | 'quiet';
  disabled?: boolean;
  loading?: boolean;
  style?: StyleProp<ViewStyle>;
}>;

export default function PrimaryButton({
  children,
  onPress,
  variant = 'primary',
  disabled = false,
  loading = false,
  style,
}: Props) {
  const theme = useAppTheme();
  const styles = useMemo(
    () =>
      StyleSheet.create({
        button: {
          alignItems: 'center',
          borderRadius: radii.md,
          justifyContent: 'center',
          minHeight: 50,
          paddingHorizontal: spacing.lg,
          paddingVertical: spacing.md,
        },
        primary: {
          backgroundColor: theme.colors.accent,
        },
        secondary: {
          backgroundColor: theme.colors.accentSoft,
          borderColor: theme.colors.border,
          borderWidth: 1,
        },
        quiet: {
          backgroundColor: theme.colors.surfaceMuted,
          borderColor: theme.colors.border,
          borderWidth: 1,
        },
        disabled: {
          opacity: 0.48,
        },
        label: {
          fontSize: 16,
          fontWeight: '700',
          letterSpacing: 0,
          textAlign: 'center',
        },
        primaryLabel: {
          color: theme.isDark ? theme.colors.background : theme.colors.surface,
        },
        secondaryLabel: {
          color: theme.colors.accent,
        },
        quietLabel: {
          color: theme.colors.ink,
        },
      }),
    [theme],
  );

  const labelStyle =
    variant === 'primary'
      ? styles.primaryLabel
      : variant === 'secondary'
        ? styles.secondaryLabel
        : styles.quietLabel;

  return (
    <Pressable
      accessibilityRole="button"
      disabled={disabled || loading}
      onPress={onPress}
      style={({ pressed }) => [
        styles.button,
        styles[variant],
        (disabled || loading) && styles.disabled,
        pressed && {
          opacity: 0.86,
          transform: [{ scale: 0.985 }],
        },
        style,
      ]}
    >
      {loading ? (
        <ActivityIndicator color={variant === 'primary' ? theme.colors.surface : theme.colors.accent} />
      ) : (
        <Text style={[styles.label, labelStyle]}>{children}</Text>
      )}
    </Pressable>
  );
}
