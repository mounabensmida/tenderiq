// Icon.jsx — quelques icônes SVG dessinées à la main (pas de bibliothèque à installer).
const PATHS = {
  logo: "M12 2 3 7v10l9 5 9-5V7l-9-5Zm0 2.3 6.5 3.6L12 11.6 5.5 7.9 12 4.3ZM5 9.6l6 3.4v6.6l-6-3.4V9.6Zm8 10V13l6-3.4v6.6l-6 3.4Z",
  search: "M10.5 3a7.5 7.5 0 0 1 5.9 12.1l4.3 4.3-1.4 1.4-4.3-4.3A7.5 7.5 0 1 1 10.5 3Zm0 2a5.5 5.5 0 1 0 0 11 5.5 5.5 0 0 0 0-11Z",
  doc: "M6 2h9l5 5v15H6V2Zm8 1.5V8h4.5L14 3.5ZM8 12h8v1.5H8V12Zm0 3.5h8V17H8v-1.5Zm0-7h4V10H8V8.5Z",
  chart: "M4 20V10h3v10H4Zm6.5 0V4h3v16h-3ZM17 20v-7h3v7h-3Z",
  mail: "M3 5h18v14H3V5Zm2 2v.3l7 4.7 7-4.7V7H5Zm14 2.7-7 4.6-7-4.6V17h14V9.7Z",
  send: "M3 20.5 21 12 3 3.5V10l12 2-12 2v6.5Z",
  logout: "M10 3h9v18h-9v-2h7V5h-7V3Zm-.5 4.5L11 9l-2 2h7v2H9l2 2-1.5 1.5L5 12l4.5-4.5Z",
  spark: "M12 2l2.2 6.3L20.5 10l-6.3 2.2L12 18.5l-2.2-6.3L3.5 10l6.3-1.7L12 2Zm7 13 1 2.8 2.8 1-2.8 1L19 22.6l-1-2.8-2.8-1 2.8-1L19 15Z",
  trophy: "M7 3h10v2h3v3a4 4 0 0 1-4 4h-.3A5 5 0 0 1 13 14.9V18h3v3H8v-3h3v-3.1A5 5 0 0 1 8.3 12H8a4 4 0 0 1-4-4V5h3V3Zm0 4H6v1a2 2 0 0 0 1 1.7V7Zm10 0v2.7A2 2 0 0 0 18 8V7h-1Z",
  wallet: "M4 5h14v3h2v11H4V5Zm2 2v10h12v-2h-4a3 3 0 0 1 0-6h4V7H6Zm8 4a1 1 0 1 0 0 2h4v-2h-4Z",
  gauge: "M12 4a9 9 0 0 1 9 9h-2a7 7 0 0 0-14 0H3a9 9 0 0 1 9-9Zm4.2 3.4 1.4 1.4-4.3 4.3a1.5 1.5 0 1 1-1.4-1.4l4.3-4.3Z",
  lock: "M7 10V7a5 5 0 0 1 10 0v3h2v11H5V10h2Zm2 0h6V7a3 3 0 0 0-6 0v3Z",
  check: "m9.5 16.6-4.6-4.6 1.4-1.4 3.2 3.2 7.7-7.7 1.4 1.4-9.1 9.1Z",
  close: "m6.4 5 5.6 5.6L17.6 5 19 6.4 13.4 12l5.6 5.6-1.4 1.4-5.6-5.6L6.4 19 5 17.6l5.6-5.6L5 6.4 6.4 5Z",
  chevron: "m9 6 6 6-6 6-1.4-1.4 4.6-4.6-4.6-4.6L9 6Z",
  shield: "M12 2 4 5v6c0 5 3.4 9.4 8 11 4.6-1.6 8-6 8-11V5l-8-3Zm-1 13.4-3.5-3.5 1.4-1.4 2.1 2.1 4.6-4.6 1.4 1.4-6 6Z",
  bolt: "M13 2 4 14h7l-1 8 9-12h-7l1-8Z",
};

export default function Icon({ name, size = 18, className = "" }) {
  return (
    <svg className={`icon ${className}`} width={size} height={size} viewBox="0 0 24 24" aria-hidden="true">
      <path d={PATHS[name]} fill="currentColor" />
    </svg>
  );
}
