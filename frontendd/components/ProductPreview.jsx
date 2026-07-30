export default function ProductPreview() {
  return (
    <div className="product-window">
      <div className="product-window-top">
        <div className="product-brand">
          <span className="product-dot" />
          ALIAS
        </div>

        <div className="product-window-controls">
          <span />
          <span />
          <span />
        </div>
      </div>

      <div className="product-window-body">
        <div className="product-sidebar">
          <div className="sidebar-active" />
          <div />
          <div />
          <div />
          <div />
        </div>

        <div className="product-content">
          <div className="product-placeholder product-wide" />

          <div className="product-placeholder-row">
            <div className="product-placeholder" />
            <div className="product-placeholder" />
          </div>

          <div className="product-placeholder product-large" />
        </div>
      </div>
    </div>
  );
}
