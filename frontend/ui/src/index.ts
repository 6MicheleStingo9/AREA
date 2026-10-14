// The design system of Kindynos: tokens and fonts (styles.css), components, language and theme.

export {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from './components/Accordion/Accordion';
export { AppHeader } from './components/AppHeader/AppHeader';
export { Badge, type BadgeTone } from './components/Badge/Badge';
export { Brand } from './components/Brand/Brand';
export { Button, ButtonLink, type ButtonVariant } from './components/Button/Button';
export { Card } from './components/Card/Card';
export { Choice, ChoiceGroup } from './components/Choice/Choice';
export { Eyebrow } from './components/Eyebrow/Eyebrow';
export { Field, TextArea, TextInput } from './components/Field/Field';
export { Heading } from './components/Heading/Heading';
export { IconButton } from './components/IconButton/IconButton';
export { LanguageSwitch } from './components/LanguageSwitch/LanguageSwitch';
export { Meter } from './components/Meter/Meter';
export { ReportFooter } from './components/ReportFooter/ReportFooter';
export {
  SegmentedControl,
  type SegmentedOption,
} from './components/SegmentedControl/SegmentedControl';
export { SkipLink } from './components/SkipLink/SkipLink';
export { ThemeToggle } from './components/ThemeToggle/ThemeToggle';
export { VisuallyHidden } from './components/VisuallyHidden/VisuallyHidden';

export { common, type CommonMessages } from './i18n/common';
export { I18nProvider } from './i18n/I18nProvider';
export { richText } from './i18n/richText';
export {
  LANGUAGES,
  translate,
  type Language,
  type MessageKey,
  type Messages,
  type Params,
} from './i18n/translate';
export { useI18n, type TypedI18n } from './i18n/useI18n';

export { type Theme } from './theme/system';
export { ThemeProvider } from './theme/ThemeProvider';
export { useTheme } from './theme/useTheme';
