function TabNav({ items, activeTab, onChange }) {
  return (
    <section className="tabs card">
      {items.map((item) => (
        <button
          key={item.key}
          className={`tab-btn ${activeTab === item.key ? "active" : ""}`}
          onClick={() => onChange(item.key)}
          type="button"
        >
          {item.label}
        </button>
      ))}
    </section>
  );
}

export default TabNav;
