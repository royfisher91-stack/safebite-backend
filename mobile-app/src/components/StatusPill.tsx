import { useMemo } from 'react';
import { StyleSheet, Text, View } from 'react-native';
import { radii, useAppTheme } from '../theme';
import { SafetyResult } from '../types/api';
import { safetyTone } from '../utils/format';

type Props = {
  result?: SafetyResult | null;
};

export default function StatusPill({ result }: Props) {
  const theme = useAppTheme();
  const tone = safetyTone(result);

  const palette =
    tone === 'safe'
      ? {
          background: theme.colors.safeSurface,
          text: theme.colors.safe,
        }
      : tone === 'avoid'
        ? {
            background: theme.colors.avoidSurface,
            text: theme.colors.avoid,
          }
        : {
            background: theme.colors.cautionSurface,
            text: theme.colors.caution,
          };

  const styles = useMemo(
    () =>
      StyleSheet.create({
        pill: {
          alignSelf: 'flex-start',
          backgroundColor: palette.background,
          borderRadius: radii.pill,
          paddingHorizontal: 12,
          paddingVertical: 7,
        },
        text: {
          color: palette.text,
          fontSize: 13,
          fontWeight: '700',
          letterSpacing: 0,
        },
      }),
    [palette.background, palette.text],
  );

  return (
    <View style={styles.pill}>
      <Text style={styles.text}>{result || 'Unknown'}</Text>
    </View>
  );
}
