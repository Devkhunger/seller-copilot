import { useLanguage } from "../i18n/LanguageContext.jsx";
export default function LanguageToggle({ dark=false }) {
  const { language, toggleLanguage } = useLanguage();
  return <button type="button" onClick={toggleLanguage} aria-label={language==="en"?"Switch to Hindi":"Switch to English"} className={dark ? "rounded-lg border border-white/20 bg-white/10 px-3 py-2 text-sm font-bold text-white" : "rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-bold text-slate-700"}>{language==="en"?"हिंदी":"English"}</button>;
}
