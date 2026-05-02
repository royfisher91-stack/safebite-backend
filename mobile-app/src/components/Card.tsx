import { PropsWithChildren, useMemo } from 'react';
import { StyleProp, StyleSheet, View, ViewStyle } from 'react-native';
import { radii, spacing, useAppTheme } from '../theme';

type Props = PropsWithChildren<{
  style?: StyleProp<ViewStyle>;
}>;

export default function Card({ children, style }: Props) {
  const theme = useAppTheme();
  const styles = useMemo(
    () =>
      StyleSheet.create({
        card: {
          backgroundColor: theme.colors.cardOverlay,
          borderColor: theme.colors.border,
          borderRadius: radii.lg,
          borderWidth: 1,
          padding: spacing.lg,
          ...theme.shadow,
        },
      }),
    [theme],
  );

  return <View style={[styles.card, style]}>{children}</View>;
}
