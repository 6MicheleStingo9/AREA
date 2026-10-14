import mark from '../../../../../files/img/brand/kindynos-mark.svg';
import wordmarkDark from '../../../../../files/img/brand/kindynos-wordmark-dark.svg';
import wordmarkLight from '../../../../../files/img/brand/kindynos-wordmark-light.svg';
import styles from './Brand.module.css';

/** The mark and the wordmark (files/img/brand/): the wordmark follows the theme */
export function Brand() {
  return (
    <span className={styles.brand}>
      <img src={mark} alt="" width="512" height="512" className={styles.mark} />
      <img src={wordmarkLight} alt="Kindynos" width="526" height="148" className={styles.light} />
      <img src={wordmarkDark} alt="Kindynos" width="526" height="148" className={styles.dark} />
    </span>
  );
}
