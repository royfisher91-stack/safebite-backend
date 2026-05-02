import {
  PropsWithChildren,
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from 'react';
import {
  createProfile as createProfileRequest,
  deleteProfile as deleteProfileRequest,
  getProfiles,
  updateProfile as updateProfileRequest,
} from '../api/client';
import { Profile, ProfileWriteInput } from '../types/api';

export type HealthOption = {
  key: string;
  label: string;
  queryValue: string;
  description: string;
};

export const CONDITION_OPTIONS: HealthOption[] = [
  {
    key: 'coeliac',
    label: 'Coeliac',
    queryValue: 'coeliac',
    description: 'Flags possible gluten-containing ingredients.',
  },
  {
    key: 'ibs',
    label: 'IBS',
    queryValue: 'ibs',
    description: 'Looks for common sensitive-stomach triggers.',
  },
  {
    key: 'stoma',
    label: 'Stoma',
    queryValue: 'stoma',
    description: 'Highlights seeds, fibres and harder-to-digest textures.',
  },
  {
    key: 'baby-specific-sensitivity',
    label: 'Baby sensitivity',
    queryValue: 'baby-specific sensitivity',
    description: 'Keeps sugar and additive checks stricter for baby-focused reviews.',
  },
];

export const ALLERGEN_OPTIONS: HealthOption[] = [
  {
    key: 'dairy',
    label: 'Dairy',
    queryValue: 'dairy',
    description: 'Matches milk, whey, casein and related dairy signals.',
  },
  {
    key: 'nuts',
    label: 'Nuts',
    queryValue: 'nuts',
    description: 'Matches tree nut and peanut allergen signals.',
  },
  {
    key: 'gluten',
    label: 'Gluten',
    queryValue: 'gluten',
    description: 'Matches gluten allergen signals.',
  },
  {
    key: 'soy',
    label: 'Soy',
    queryValue: 'soy',
    description: 'Matches soy and soya allergen signals.',
  },
  {
    key: 'egg',
    label: 'Egg',
    queryValue: 'egg',
    description: 'Matches egg allergen signals.',
  },
];

type HealthPreferencesContextValue = {
  profiles: Profile[];
  profilesLoading: boolean;
  activeProfile: Profile | null;
  activeProfileId: number | null;
  selectedAllergens: string[];
  selectedConditions: string[];
  activeCount: number;
  toggleAllergen: (value: string) => void;
  toggleCondition: (value: string) => void;
  isAllergenSelected: (value: string) => boolean;
  isConditionSelected: (value: string) => boolean;
  selectProfile: (profileId: number | null) => void;
  createProfile: (input: ProfileWriteInput) => Promise<Profile>;
  updateProfile: (profileId: number, input: ProfileWriteInput) => Promise<Profile>;
  deleteProfile: (profileId: number) => Promise<void>;
  reloadProfiles: (preferredProfileId?: number | null) => Promise<void>;
  clearPreferences: () => void;
};

const HealthPreferencesContext = createContext<HealthPreferencesContextValue | undefined>(undefined);

function uniqueValues(values: string[]): string[] {
  const seen = new Set<string>();
  const result: string[] = [];

  values.forEach((value) => {
    const trimmed = value.trim();
    if (!trimmed) {
      return;
    }

    const key = trimmed.toLowerCase();
    if (seen.has(key)) {
      return;
    }

    seen.add(key);
    result.push(trimmed);
  });

  return result;
}

function toggleValue(values: string[], value: string): string[] {
  return values.includes(value)
    ? values.filter((item) => item !== value)
    : uniqueValues([...values, value]);
}

export function HealthPreferencesProvider({ children }: PropsWithChildren) {
  const [profiles, setProfiles] = useState<Profile[]>([]);
  const [profilesLoading, setProfilesLoading] = useState(true);
  const [activeProfileId, setActiveProfileId] = useState<number | null>(null);
  const [selectedAllergens, setSelectedAllergens] = useState<string[]>([]);
  const [selectedConditions, setSelectedConditions] = useState<string[]>([]);

  const syncSelectionsFromProfile = useCallback((profile: Profile | null) => {
    if (!profile) {
      return;
    }
    setSelectedAllergens(uniqueValues(profile.allergies ?? []));
    setSelectedConditions(uniqueValues(profile.conditions ?? []));
  }, []);

  const reloadProfiles = useCallback(
    async (preferredProfileId?: number | null) => {
      setProfilesLoading(true);

      try {
        const nextProfiles = await getProfiles();
        setProfiles(nextProfiles);

        const chosenId =
          preferredProfileId === undefined
            ? activeProfileId
            : preferredProfileId;

        if (chosenId === null) {
          setActiveProfileId(null);
          setProfilesLoading(false);
          return;
        }

        const chosenProfile =
          nextProfiles.find((profile) => profile.id === chosenId) ??
          nextProfiles.find((profile) => profile.is_default) ??
          null;

        if (chosenProfile) {
          setActiveProfileId(chosenProfile.id);
          syncSelectionsFromProfile(chosenProfile);
        } else if (!nextProfiles.length) {
          setActiveProfileId(null);
        }
      } finally {
        setProfilesLoading(false);
      }
    },
    [activeProfileId, syncSelectionsFromProfile],
  );

  useEffect(() => {
    reloadProfiles().catch(() => {
      setProfiles([]);
      setProfilesLoading(false);
    });
  }, [reloadProfiles]);

  const activeProfile = useMemo(
    () => profiles.find((profile) => profile.id === activeProfileId) ?? null,
    [activeProfileId, profiles],
  );

  const value = useMemo<HealthPreferencesContextValue>(
    () => ({
      profiles,
      profilesLoading,
      activeProfile,
      activeProfileId,
      selectedAllergens,
      selectedConditions,
      activeCount: selectedAllergens.length + selectedConditions.length,
      toggleAllergen: (nextValue) => setSelectedAllergens((current) => toggleValue(current, nextValue)),
      toggleCondition: (nextValue) => setSelectedConditions((current) => toggleValue(current, nextValue)),
      isAllergenSelected: (nextValue) => selectedAllergens.includes(nextValue),
      isConditionSelected: (nextValue) => selectedConditions.includes(nextValue),
      selectProfile: (profileId) => {
        setActiveProfileId(profileId);
        const profile = profiles.find((item) => item.id === profileId) ?? null;
        if (profile) {
          syncSelectionsFromProfile(profile);
        }
      },
      createProfile: async (input) => {
        const created = await createProfileRequest({
          ...input,
          allergies: uniqueValues(input.allergies ?? []),
          conditions: uniqueValues(input.conditions ?? []),
        });
        await reloadProfiles(created.id);
        return created;
      },
      updateProfile: async (profileId, input) => {
        const updated = await updateProfileRequest(profileId, {
          ...input,
          allergies: uniqueValues(input.allergies ?? []),
          conditions: uniqueValues(input.conditions ?? []),
        });
        await reloadProfiles(updated.id);
        return updated;
      },
      deleteProfile: async (profileId) => {
        const deletingActive = activeProfileId === profileId;
        await deleteProfileRequest(profileId);
        if (deletingActive) {
          setActiveProfileId(null);
        }
        await reloadProfiles(deletingActive ? undefined : activeProfileId);
        if (deletingActive && profiles.length <= 1) {
          setSelectedAllergens([]);
          setSelectedConditions([]);
        }
      },
      reloadProfiles,
      clearPreferences: () => {
        setActiveProfileId(null);
        setSelectedAllergens([]);
        setSelectedConditions([]);
      },
    }),
    [
      profiles,
      profilesLoading,
      activeProfile,
      activeProfileId,
      selectedAllergens,
      selectedConditions,
      reloadProfiles,
      syncSelectionsFromProfile,
    ],
  );

  return (
    <HealthPreferencesContext.Provider value={value}>
      {children}
    </HealthPreferencesContext.Provider>
  );
}

export function useHealthPreferences() {
  const context = useContext(HealthPreferencesContext);

  if (!context) {
    throw new Error('useHealthPreferences must be used inside HealthPreferencesProvider');
  }

  return context;
}
