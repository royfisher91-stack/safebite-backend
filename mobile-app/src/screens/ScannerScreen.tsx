import { useMemo, useState } from 'react';
import { Alert, StyleSheet, Text, TextInput, View } from 'react-native';
import { CameraView, useCameraPermissions } from 'expo-camera';
import Card from '../components/Card';
import FadeInView from '../components/FadeInView';
import PrimaryButton from '../components/PrimaryButton';
import Screen from '../components/Screen';
import { MainTabScreenProps } from '../navigation/RootNavigator';
import { AppTheme, radii, spacing, useAppTheme } from '../theme';

type Props = MainTabScreenProps<'Scanner'>;

export default function ScannerScreen({ navigation }: Props) {
  const theme = useAppTheme();
  const styles = useMemo(() => createStyles(theme), [theme]);
  const sharedStyles = theme.sharedStyles;
  const [permission, requestPermission] = useCameraPermissions();
  const [manualBarcode, setManualBarcode] = useState('5056000505910');
  const [scannedBarcode, setScannedBarcode] = useState<string | null>(null);

  function openBarcode(barcode: string) {
    const value = barcode.trim();

    if (!value) {
      Alert.alert('Enter a barcode');
      return;
    }

    setScannedBarcode(value);
    navigation.navigate('ProductDetail', { barcode: value, shouldSaveHistory: true });
  }

  return (
    <Screen>
      <FadeInView>
        <Text style={sharedStyles.screenTitle}>Scanner</Text>
        <Text style={styles.subtitle}>Use the camera for a fast check, with a clean manual fallback underneath.</Text>
      </FadeInView>

      <FadeInView delay={40}>
        <Card style={styles.cameraCard}>
          {permission?.granted ? (
            <View style={styles.cameraFrame}>
              <CameraView
                barcodeScannerSettings={{
                  barcodeTypes: ['ean13', 'ean8', 'upc_a', 'upc_e'],
                }}
                onBarcodeScanned={
                  scannedBarcode
                    ? undefined
                    : ({ data }) => {
                        openBarcode(data);
                      }
                }
                style={styles.camera}
              />
              <View pointerEvents="none" style={styles.scanWindow} />
              <View pointerEvents="none" style={styles.scanLine} />
            </View>
          ) : (
            <View style={styles.permissionBlock}>
              <Text style={sharedStyles.body}>Camera access is off right now.</Text>
              <PrimaryButton onPress={requestPermission} style={styles.permissionButton}>
                Allow camera
              </PrimaryButton>
            </View>
          )}

          {scannedBarcode ? (
            <PrimaryButton
              onPress={() => setScannedBarcode(null)}
              style={styles.scanAgainButton}
              variant="secondary"
            >
              Scan another
            </PrimaryButton>
          ) : null}
        </Card>
      </FadeInView>

      <FadeInView delay={80}>
        <Card>
          <Text style={styles.label}>Manual fallback</Text>
          <TextInput
            autoCapitalize="none"
            autoCorrect={false}
            keyboardType="number-pad"
            onChangeText={setManualBarcode}
            placeholder="Enter barcode"
            placeholderTextColor={theme.colors.muted}
            style={styles.input}
            value={manualBarcode}
          />
          <PrimaryButton onPress={() => openBarcode(manualBarcode)}>
            Open product
          </PrimaryButton>
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
      lineHeight: 22,
      marginTop: spacing.sm,
    },
    cameraCard: {
      marginTop: spacing.xl,
      marginBottom: spacing.lg,
    },
    cameraFrame: {
      aspectRatio: 1,
      backgroundColor: theme.colors.ink,
      borderRadius: radii.lg,
      overflow: 'hidden',
    },
    camera: {
      flex: 1,
    },
    scanWindow: {
      borderColor: 'rgba(255,255,255,0.72)',
      borderRadius: radii.md,
      borderWidth: 2,
      bottom: '22%',
      left: '12%',
      position: 'absolute',
      right: '12%',
      top: '22%',
    },
    scanLine: {
      alignSelf: 'center',
      backgroundColor: theme.colors.surface,
      borderRadius: radii.pill,
      height: 3,
      opacity: 0.82,
      position: 'absolute',
      top: '50%',
      width: '68%',
    },
    permissionBlock: {
      gap: spacing.md,
    },
    permissionButton: {
      alignSelf: 'stretch',
    },
    scanAgainButton: {
      marginTop: spacing.md,
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
      marginBottom: spacing.md,
      minHeight: 52,
      paddingHorizontal: 16,
    },
  });
}
