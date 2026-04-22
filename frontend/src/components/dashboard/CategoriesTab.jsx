function CategoriesTab({ categoryForm, setCategoryForm, createCategory, categories }) {
  return (
    <section className="grid two-cols">
      <form className="card form" onSubmit={createCategory}>
        <h3 className="section-title">Tạo danh mục</h3>
        <label className="field-label">Tên danh mục</label>
        <input
          value={categoryForm.name}
          onChange={(event) => setCategoryForm({ ...categoryForm, name: event.target.value })}
          required
        />
        <label className="field-label">Loại</label>
        <select
          value={categoryForm.type}
          onChange={(event) => setCategoryForm({ ...categoryForm, type: event.target.value })}
        >
          <option value="expense">Chi tiêu</option>
          <option value="income">Thu nhập</option>
        </select>
        <label className="field-label">Danh mục cha (optional)</label>
        <select
          value={categoryForm.parent_id}
          onChange={(event) => setCategoryForm({ ...categoryForm, parent_id: event.target.value })}
        >
          <option value="">Không có</option>
          {categories.map((item) => (
            <option key={item.id} value={item.id}>{item.name}</option>
          ))}
        </select>
        <label className="field-label">Icon (optional)</label>
        <input
          value={categoryForm.icon}
          onChange={(event) => setCategoryForm({ ...categoryForm, icon: event.target.value })}
          placeholder="coffee, car, gift..."
        />
        <button className="btn btn-primary" type="submit">Tạo danh mục</button>
      </form>

      <article className="card">
        <h3 className="section-title">Danh mục hiện có</h3>
        <div className="chip-wrap">
          {categories.map((item) => (
            <span key={item.id} className={`chip ${item.is_system ? "chip-system" : "chip-custom"}`}>
              {item.name} ({item.type === "expense" ? "Chi" : "Thu"})
            </span>
          ))}
        </div>
      </article>
    </section>
  );
}

export default CategoriesTab;
