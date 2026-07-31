export default function StatusDot({
  active = false,
  label,
}) {
  return (
    <div className="alias-status">
      <span
        className={`alias-status-indicator ${
          active ? "is-active" : "is-inactive"
        }`}
      />

      <span className="alias-status-label">
        {label}
      </span>
    </div>
  );
}
