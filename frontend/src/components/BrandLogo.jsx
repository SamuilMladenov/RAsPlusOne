/** TriageFlow horizontal logo (public/triageflow-logo.png). */
export default function BrandLogo({ className = "", size = "default" }) {
  const height =
    size === "large" ? "h-14 md:h-16" : size === "compact" ? "h-8" : "h-10 md:h-11";
  return (
    <img
      src="/triageflow-logo.png"
      alt="TriageFlow"
      className={`w-auto max-w-full object-contain object-left ${height} ${className}`}
    />
  );
}
