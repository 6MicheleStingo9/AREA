import type { CommonMessages } from '../../i18n/common';
import { LANGUAGES } from '../../i18n/translate';
import { useI18n } from '../../i18n/useI18n';
import { SegmentedControl } from '../SegmentedControl/SegmentedControl';

/** The language of the interface, as EN and IT: each read by its name, in its own language */
export function LanguageSwitch() {
  const { lang, setLang, t } = useI18n<CommonMessages>();
  const options = LANGUAGES.map((value) => ({
    value,
    label: value.toUpperCase(),
    ariaLabel: t(`common.language.${value}`),
    lang: value,
  }));
  return (
    <SegmentedControl
      legend={t('common.language.label')}
      hideLegend
      options={options}
      value={lang}
      onChange={setLang}
    />
  );
}
