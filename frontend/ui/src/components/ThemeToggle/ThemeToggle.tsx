import { Moon, Sun } from 'lucide-react';
import type { CommonMessages } from '../../i18n/common';
import { useI18n } from '../../i18n/useI18n';
import { useTheme } from '../../theme/useTheme';
import { IconButton } from '../IconButton/IconButton';

/** Switches between the light and the dark theme; its icon shows the theme it switches to */
export function ThemeToggle() {
  const { theme, toggle } = useTheme();
  const { t } = useI18n<CommonMessages>();
  const toDark = theme === 'light';
  return (
    <IconButton
      label={t(toDark ? 'common.theme.to_dark' : 'common.theme.to_light')}
      onClick={toggle}
    >
      {toDark ? <Moon /> : <Sun />}
    </IconButton>
  );
}
