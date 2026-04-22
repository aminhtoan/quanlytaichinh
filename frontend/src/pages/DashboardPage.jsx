import { useEffect, useMemo, useState } from "react";
import AssistantTab from "../components/dashboard/AssistantTab";
import BudgetsTab from "../components/dashboard/BudgetsTab";
import CategoriesTab from "../components/dashboard/CategoriesTab";
import DashboardHeader from "../components/dashboard/DashboardHeader";
import DebtsTab from "../components/dashboard/DebtsTab";
import InvestmentsTab from "../components/dashboard/InvestmentsTab";
import OverviewTab from "../components/dashboard/OverviewTab";
import SubscriptionsTab from "../components/dashboard/SubscriptionsTab";
import TabNav from "../components/dashboard/TabNav";
import TransactionsTab from "../components/dashboard/TransactionsTab";
import WalletsTab from "../components/dashboard/WalletsTab";
import api from "../services/api";

const TAB_ITEMS = [
  { key: "overview", label: "Tổng quan" },
  { key: "transactions", label: "Giao dịch" },
  { key: "wallets", label: "Ví" },
  { key: "categories", label: "Danh mục" },
  { key: "budgets", label: "Ngân sách" },
  { key: "subscriptions", label: "Định kỳ" },
  { key: "investments", label: "Đầu tư" },
  { key: "debts", label: "Công nợ" },
  { key: "assistant", label: "Trợ lý AI" },
];

const nowLocal = () => new Date().toISOString().slice(0, 16);
const todayLocal = () => new Date().toISOString().slice(0, 10);

function DashboardPage({ onLogout }) {
  const [user, setUser] = useState(null);
  const [activeTab, setActiveTab] = useState("overview");
  const [loading, setLoading] = useState(false);
  const [notice, setNotice] = useState({ type: "", text: "" });

  const [wallets, setWallets] = useState([]);
  const [categories, setCategories] = useState([]);
  const [transactions, setTransactions] = useState([]);
  const [summary, setSummary] = useState({ total_income: 0, total_expense: 0, balance: 0 });
  const [insights, setInsights] = useState({ recommendations: [], anomalies: [] });

  const [queryResult, setQueryResult] = useState({ items: [], total: 0, page: 1, size: 20 });
  const [debts, setDebts] = useState([]);
  const [subscriptions, setSubscriptions] = useState([]);
  const [subscriptionSuggestions, setSubscriptionSuggestions] = useState([]);
  const [budgetProgress, setBudgetProgress] = useState([]);

  const [transactionForm, setTransactionForm] = useState({
    type: "expense",
    amount: "",
    wallet_id: "",
    category_id: "",
    category: "",
    note: "",
    transaction_date: nowLocal(),
  });

  const [queryForm, setQueryForm] = useState({
    start_date: "",
    end_date: "",
    wallet_id: "",
    type: "",
    page: 1,
    size: 20,
  });

  const [transferForm, setTransferForm] = useState({
    source_wallet_id: "",
    dest_wallet_id: "",
    amount: "",
    note: "",
    date: nowLocal(),
  });

  const [walletForm, setWalletForm] = useState({
    name: "",
    type: "cash",
    currency: "VND",
    initial_balance: "0",
  });

  const [categoryForm, setCategoryForm] = useState({
    name: "",
    type: "expense",
    parent_id: "",
    icon: "",
  });

  const [budgetForm, setBudgetForm] = useState({
    category_id: "",
    amount_limit: "",
    period: "monthly",
    start_date: todayLocal(),
    end_date: todayLocal(),
  });

  const [subscriptionForm, setSubscriptionForm] = useState({
    name: "",
    amount: "",
    frequency: "monthly",
    default_wallet_id: "",
    next_due_date: "",
  });

  const [debtForm, setDebtForm] = useState({
    creditor_name: "",
    total_amount: "",
    type: "payable",
    wallet_id: "",
  });

  const [repayForm, setRepayForm] = useState({
    debt_id: "",
    amount: "",
    wallet_id: "",
    date: "",
  });

  const [investmentCreateForm, setInvestmentCreateForm] = useState({
    wallet_id: "",
    name: "",
    type: "gold",
    principal_amount: "",
  });
  const [investmentUpdateForm, setInvestmentUpdateForm] = useState({
    investment_id: "",
    current_value: "",
  });
  const [investmentSellForm, setInvestmentSellForm] = useState({
    investment_id: "",
    selling_price: "",
    wallet_id: "",
    date: "",
  });
  const [investmentOutcome, setInvestmentOutcome] = useState(null);

  const [aiParseText, setAiParseText] = useState("");
  const [aiParseResult, setAiParseResult] = useState(null);
  const [ocrFile, setOcrFile] = useState(null);
  const [ocrWalletId, setOcrWalletId] = useState("");
  const [ocrResult, setOcrResult] = useState(null);
  const [chatMessage, setChatMessage] = useState("");
  const [chatReply, setChatReply] = useState("");
  const [chatSessionId, setChatSessionId] = useState("");
  const [chatHistory, setChatHistory] = useState([]);
  const [chatChartData, setChatChartData] = useState(null);
  const [chatLoading, setChatLoading] = useState(false);

  const formatCurrency = (value) => `${Number(value || 0).toLocaleString("vi-VN")} ₫`;
  const formatDate = (value) => new Date(value).toLocaleString("vi-VN");

  const categoryById = useMemo(() => {
    return categories.reduce((acc, item) => {
      acc[item.id] = item;
      return acc;
    }, {});
  }, [categories]);

  const showNotice = (type, text) => {
    setNotice({ type, text });
  };

  const toErrorMessage = (error, fallback = "Đã có lỗi xảy ra") => {
    return error?.response?.data?.detail || fallback;
  };

  const safeGet = async (path, fallbackValue) => {
    try {
      const response = await api.get(path);
      return response.data;
    } catch {
      return fallbackValue;
    }
  };

  const loadAllData = async () => {
    const meResponse = await api.get("/auth/me");
    setUser(meResponse.data);

    const [
      walletsData,
      categoriesData,
      transactionsData,
      summaryData,
      insightsData,
      debtsData,
      subscriptionsData,
      budgetData,
      subscriptionDetectData,
      queryData,
    ] = await Promise.all([
      safeGet("/wallets", []),
      safeGet("/categories", []),
      safeGet("/transactions", []),
      safeGet("/transactions/summary/overview", { total_income: 0, total_expense: 0, balance: 0 }),
      safeGet("/ai/insights", { recommendations: [], anomalies: [] }),
      safeGet("/debts", []),
      safeGet("/subscriptions", []),
      safeGet("/budgets/progress?period=monthly", []),
      safeGet("/subscriptions/detect", []),
      safeGet("/transactions/query?page=1&size=20", { items: [], total: 0, page: 1, size: 20 }),
    ]);

    setWallets(walletsData);
    setCategories(categoriesData);
    setTransactions(transactionsData);
    setSummary(summaryData);
    setInsights(insightsData);
    setDebts(debtsData);
    setSubscriptions(subscriptionsData);
    setBudgetProgress(budgetData);
    setSubscriptionSuggestions(subscriptionDetectData);
    setQueryResult(queryData);
  };

  useEffect(() => {
    const bootstrap = async () => {
      setLoading(true);
      try {
        await loadAllData();
      } catch {
        onLogout();
      } finally {
        setLoading(false);
      }
    };

    bootstrap();
  }, []);

  useEffect(() => {
    if (!wallets.length) {
      return;
    }

    setTransactionForm((prev) => (prev.wallet_id ? prev : { ...prev, wallet_id: wallets[0].id }));
    setTransferForm((prev) => {
      if (prev.source_wallet_id || prev.dest_wallet_id || wallets.length < 2) {
        return prev;
      }
      return {
        ...prev,
        source_wallet_id: wallets[0].id,
        dest_wallet_id: wallets[1].id,
      };
    });
    setSubscriptionForm((prev) => (prev.default_wallet_id ? prev : { ...prev, default_wallet_id: wallets[0].id }));
    setDebtForm((prev) => (prev.wallet_id ? prev : { ...prev, wallet_id: wallets[0].id }));
    setRepayForm((prev) => (prev.wallet_id ? prev : { ...prev, wallet_id: wallets[0].id }));
    setInvestmentCreateForm((prev) => (prev.wallet_id ? prev : { ...prev, wallet_id: wallets[0].id }));
    setInvestmentSellForm((prev) => (prev.wallet_id ? prev : { ...prev, wallet_id: wallets[0].id }));
    setOcrWalletId((prev) => (prev ? prev : wallets[0].id));
  }, [wallets]);

  useEffect(() => {
    if (!categories.length) {
      return;
    }
    setTransactionForm((prev) => {
      if (prev.category_id) {
        return prev;
      }
      const firstExpenseCategory = categories.find((item) => item.type === "expense") || categories[0];
      return {
        ...prev,
        category_id: firstExpenseCategory?.id || "",
        category: firstExpenseCategory?.name || "",
      };
    });

    setBudgetForm((prev) => {
      if (prev.category_id) {
        return prev;
      }
      const firstExpenseCategory = categories.find((item) => item.type === "expense") || categories[0];
      return { ...prev, category_id: firstExpenseCategory?.id || "" };
    });
  }, [categories]);

  useEffect(() => {
    if (!debts.length) {
      return;
    }
    setRepayForm((prev) => (prev.debt_id ? prev : { ...prev, debt_id: debts[0].id }));
  }, [debts]);

  const createTransaction = async (event) => {
    event.preventDefault();
    try {
      const selectedCategory = categoryById[transactionForm.category_id];
      const categoryName = transactionForm.category || selectedCategory?.name || "Khác";

      await api.post("/transactions", {
        type: transactionForm.type,
        amount: Number(transactionForm.amount),
        wallet_id: transactionForm.wallet_id || null,
        category_id: transactionForm.category_id || null,
        category: categoryName,
        note: transactionForm.note,
        transaction_date: new Date(transactionForm.transaction_date).toISOString(),
      });

      setTransactionForm((prev) => ({
        ...prev,
        amount: "",
        note: "",
        transaction_date: nowLocal(),
      }));
      showNotice("success", "Đã thêm giao dịch thành công.");
      await loadAllData();
    } catch (error) {
      showNotice("error", toErrorMessage(error, "Không thể thêm giao dịch"));
    }
  };

  const runTransactionQuery = async () => {
    try {
      const params = new URLSearchParams();
      params.append("page", String(queryForm.page || 1));
      params.append("size", String(queryForm.size || 20));

      if (queryForm.start_date) {
        params.append("start_date", `${queryForm.start_date}T00:00:00`);
      }
      if (queryForm.end_date) {
        params.append("end_date", `${queryForm.end_date}T23:59:59`);
      }
      if (queryForm.wallet_id) {
        params.append("wallet_id", queryForm.wallet_id);
      }
      if (queryForm.type) {
        params.append("type", queryForm.type);
      }

      const response = await api.get(`/transactions/query?${params.toString()}`);
      setQueryResult(response.data);
      showNotice("success", "Đã lọc giao dịch thành công.");
    } catch (error) {
      showNotice("error", toErrorMessage(error, "Không thể lọc giao dịch"));
    }
  };

  const submitTransfer = async (event) => {
    event.preventDefault();
    try {
      await api.post("/transactions/transfer", {
        source_wallet_id: transferForm.source_wallet_id,
        dest_wallet_id: transferForm.dest_wallet_id,
        amount: Number(transferForm.amount),
        note: transferForm.note || "Chuyển tiền nội bộ",
        date: new Date(transferForm.date).toISOString(),
      });

      setTransferForm((prev) => ({ ...prev, amount: "", note: "", date: nowLocal() }));
      showNotice("success", "Chuyển tiền thành công.");
      await loadAllData();
    } catch (error) {
      showNotice("error", toErrorMessage(error, "Không thể chuyển tiền"));
    }
  };

  const removeTransaction = async (id) => {
    try {
      await api.delete(`/transactions/${id}`);
      showNotice("success", "Đã xóa giao dịch.");
      await loadAllData();
    } catch (error) {
      showNotice("error", toErrorMessage(error, "Không thể xóa giao dịch"));
    }
  };

  const createWallet = async (event) => {
    event.preventDefault();
    try {
      await api.post("/wallets", {
        name: walletForm.name,
        type: walletForm.type,
        currency: walletForm.currency,
        initial_balance: Number(walletForm.initial_balance || 0),
      });
      setWalletForm({ name: "", type: "cash", currency: "VND", initial_balance: "0" });
      showNotice("success", "Đã tạo ví mới.");
      await loadAllData();
    } catch (error) {
      showNotice("error", toErrorMessage(error, "Không thể tạo ví"));
    }
  };

  const deleteWallet = async (walletId) => {
    try {
      await api.delete(`/wallets/${walletId}`);
      showNotice("success", "Đã xóa ví.");
      await loadAllData();
    } catch (error) {
      showNotice("error", toErrorMessage(error, "Không thể xóa ví"));
    }
  };

  const createCategory = async (event) => {
    event.preventDefault();
    try {
      await api.post("/categories", {
        name: categoryForm.name,
        type: categoryForm.type,
        parent_id: categoryForm.parent_id || null,
        icon: categoryForm.icon || null,
      });
      setCategoryForm((prev) => ({ ...prev, name: "", parent_id: "", icon: "" }));
      showNotice("success", "Đã tạo danh mục.");
      await loadAllData();
    } catch (error) {
      showNotice("error", toErrorMessage(error, "Không thể tạo danh mục"));
    }
  };

  const createBudget = async (event) => {
    event.preventDefault();
    try {
      await api.post("/budgets", {
        category_id: budgetForm.category_id,
        amount_limit: Number(budgetForm.amount_limit),
        period: budgetForm.period,
        start_date: `${budgetForm.start_date}T00:00:00.000Z`,
        end_date: `${budgetForm.end_date}T23:59:59.000Z`,
      });
      showNotice("success", "Đã tạo ngân sách.");
      await loadAllData();
    } catch (error) {
      showNotice("error", toErrorMessage(error, "Không thể tạo ngân sách"));
    }
  };

  const createSubscription = async (event) => {
    event.preventDefault();
    try {
      await api.post("/subscriptions", {
        name: subscriptionForm.name,
        amount: Number(subscriptionForm.amount),
        frequency: subscriptionForm.frequency,
        default_wallet_id: subscriptionForm.default_wallet_id || null,
        next_due_date: subscriptionForm.next_due_date
          ? new Date(subscriptionForm.next_due_date).toISOString()
          : null,
      });
      setSubscriptionForm((prev) => ({ ...prev, name: "", amount: "", next_due_date: "" }));
      showNotice("success", "Đã tạo khoản định kỳ.");
      await loadAllData();
    } catch (error) {
      showNotice("error", toErrorMessage(error, "Không thể tạo khoản định kỳ"));
    }
  };

  const toggleSubscription = async (item) => {
    try {
      await api.put(`/subscriptions/${item.id}`, { is_active: !item.is_active });
      showNotice("success", "Đã cập nhật trạng thái subscription.");
      await loadAllData();
    } catch (error) {
      showNotice("error", toErrorMessage(error, "Không thể cập nhật subscription"));
    }
  };

  const removeSubscription = async (subscriptionId) => {
    try {
      await api.delete(`/subscriptions/${subscriptionId}`);
      showNotice("success", "Đã ngưng subscription.");
      await loadAllData();
    } catch (error) {
      showNotice("error", toErrorMessage(error, "Không thể xóa subscription"));
    }
  };

  const createDebt = async (event) => {
    event.preventDefault();
    try {
      await api.post("/debts", {
        creditor_name: debtForm.creditor_name,
        total_amount: Number(debtForm.total_amount),
        type: debtForm.type,
        wallet_id: debtForm.wallet_id,
      });
      setDebtForm((prev) => ({ ...prev, creditor_name: "", total_amount: "" }));
      showNotice("success", "Đã tạo khoản công nợ.");
      await loadAllData();
    } catch (error) {
      showNotice("error", toErrorMessage(error, "Không thể tạo khoản công nợ"));
    }
  };

  const repayDebt = async (event) => {
    event.preventDefault();
    try {
      await api.post(`/debts/${repayForm.debt_id}/repay`, {
        amount: Number(repayForm.amount),
        wallet_id: repayForm.wallet_id,
        date: repayForm.date ? new Date(repayForm.date).toISOString() : null,
      });
      setRepayForm((prev) => ({ ...prev, amount: "", date: "" }));
      showNotice("success", "Thanh toán công nợ thành công.");
      await loadAllData();
    } catch (error) {
      showNotice("error", toErrorMessage(error, "Không thể thanh toán công nợ"));
    }
  };

  const createInvestment = async (event) => {
    event.preventDefault();
    try {
      const response = await api.post("/investments", {
        wallet_id: investmentCreateForm.wallet_id,
        name: investmentCreateForm.name,
        type: investmentCreateForm.type,
        principal_amount: Number(investmentCreateForm.principal_amount),
      });

      const createdId = response?.data?.id || "";
      setInvestmentUpdateForm((prev) => ({ ...prev, investment_id: createdId || prev.investment_id }));
      setInvestmentSellForm((prev) => ({ ...prev, investment_id: createdId || prev.investment_id }));
      setInvestmentOutcome({
        action: "Tạo khoản đầu tư",
        data: response.data,
      });
      setInvestmentCreateForm((prev) => ({ ...prev, name: "", principal_amount: "" }));
      showNotice("success", "Đã tạo khoản đầu tư.");
      await loadAllData();
    } catch (error) {
      showNotice("error", toErrorMessage(error, "Không thể tạo khoản đầu tư"));
    }
  };

  const updateInvestment = async (event) => {
    event.preventDefault();
    try {
      const response = await api.put(`/investments/${investmentUpdateForm.investment_id}/update`, {
        current_value: Number(investmentUpdateForm.current_value),
      });
      setInvestmentOutcome({ action: "Cập nhật giá trị đầu tư", data: response.data });
      showNotice("success", "Đã cập nhật giá trị đầu tư.");
      await loadAllData();
    } catch (error) {
      showNotice("error", toErrorMessage(error, "Không thể cập nhật đầu tư"));
    }
  };

  const sellInvestment = async (event) => {
    event.preventDefault();
    try {
      const response = await api.post(`/investments/${investmentSellForm.investment_id}/transactions`, {
        selling_price: Number(investmentSellForm.selling_price),
        wallet_id: investmentSellForm.wallet_id,
        date: investmentSellForm.date ? new Date(investmentSellForm.date).toISOString() : null,
      });
      setInvestmentOutcome({ action: "Chốt đầu tư", data: response.data });
      showNotice("success", "Đã chốt khoản đầu tư.");
      await loadAllData();
    } catch (error) {
      showNotice("error", toErrorMessage(error, "Không thể chốt đầu tư"));
    }
  };

  const parseAiText = async () => {
    if (!aiParseText.trim()) {
      return;
    }
    try {
      const response = await api.post("/ai/parse", { text: aiParseText });
      setAiParseResult(response.data);
      showNotice("success", "Đã phân tích câu lệnh AI.");
    } catch (error) {
      showNotice("error", toErrorMessage(error, "Không thể phân tích AI"));
    }
  };

  const scanOcr = async () => {
    if (!ocrFile) {
      return;
    }

    const formData = new FormData();
    formData.append("file", ocrFile);
    formData.append("auto_save", "true");
    if (ocrWalletId) {
      formData.append("wallet_id", ocrWalletId);
    }

    try {
      const response = await api.post("/ai/ocr", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setOcrResult(response.data);
      if (response.data?.auto_saved) {
        showNotice("success", "Đã quét OCR và tự thêm vào mục Giao dịch.");
        await loadAllData();
      } else {
        showNotice("error", response.data?.auto_save_reason || "OCR thành công nhưng chưa tự lưu giao dịch.");
      }
    } catch (error) {
      showNotice("error", toErrorMessage(error, "Không thể quét OCR"));
    }
  };

  const loadChatHistory = async (sessionId) => {
    if (!sessionId) {
      return;
    }
    try {
      const response = await api.get(`/ai/chat/${sessionId}`);
      setChatHistory(response.data || []);
    } catch {
      setChatHistory([]);
    }
  };

  const askChatbot = async () => {
    if (!chatMessage.trim()) {
      showNotice("error", "Vui lòng nhập câu hỏi cho chatbot.");
      return;
    }

    setChatLoading(true);
    setChatReply("");
    try {
      const response = await api.post("/chat/ask", {
        message: chatMessage.trim(),
        session_id: chatSessionId || null,
      });

      const newSessionId = response?.data?.session_id || chatSessionId;
      setChatReply(response?.data?.reply || "");
      setChatChartData(response?.data?.chart_data || null);
      setChatSessionId(newSessionId);
      await loadChatHistory(newSessionId);
      showNotice("success", "Đã nhận phản hồi từ trợ lý AI.");
    } catch (error) {
      showNotice("error", toErrorMessage(error, "Không thể kết nối chatbot"));
    } finally {
      setChatLoading(false);
    }
  };

  const recentTransactions = transactions.slice(0, 8);
  const activeDebts = debts.filter((item) => item.status === "active").length;
  const activeSubscriptions = subscriptions.filter((item) => item.is_active).length;

  return (
    <div className="container page-shell">
      <DashboardHeader user={user} onLogout={onLogout} />

      <TabNav items={TAB_ITEMS} activeTab={activeTab} onChange={setActiveTab} />

      {notice.text && (
        <section className={`notice ${notice.type === "error" ? "error" : "success"}`}>
          {notice.text}
        </section>
      )}

      {loading && <section className="notice">Đang tải dữ liệu...</section>}

      {activeTab === "overview" && (
        <OverviewTab
          summary={summary}
          wallets={wallets}
          activeDebts={activeDebts}
          activeSubscriptions={activeSubscriptions}
          insights={insights}
          recentTransactions={recentTransactions}
          formatCurrency={formatCurrency}
          formatDate={formatDate}
        />
      )}

      {activeTab === "transactions" && (
        <TransactionsTab
          transactionForm={transactionForm}
          setTransactionForm={setTransactionForm}
          createTransaction={createTransaction}
          transferForm={transferForm}
          setTransferForm={setTransferForm}
          submitTransfer={submitTransfer}
          queryForm={queryForm}
          setQueryForm={setQueryForm}
          runTransactionQuery={runTransactionQuery}
          wallets={wallets}
          categories={categories}
          queryResult={queryResult}
          formatDate={formatDate}
          formatCurrency={formatCurrency}
          removeTransaction={removeTransaction}
        />
      )}

      {activeTab === "wallets" && (
        <WalletsTab
          walletForm={walletForm}
          setWalletForm={setWalletForm}
          createWallet={createWallet}
          wallets={wallets}
          deleteWallet={deleteWallet}
          formatCurrency={formatCurrency}
        />
      )}

      {activeTab === "categories" && (
        <CategoriesTab
          categoryForm={categoryForm}
          setCategoryForm={setCategoryForm}
          createCategory={createCategory}
          categories={categories}
        />
      )}

      {activeTab === "budgets" && (
        <BudgetsTab
          budgetForm={budgetForm}
          setBudgetForm={setBudgetForm}
          createBudget={createBudget}
          categories={categories}
          budgetProgress={budgetProgress}
          formatCurrency={formatCurrency}
        />
      )}

      {activeTab === "subscriptions" && (
        <SubscriptionsTab
          subscriptionForm={subscriptionForm}
          setSubscriptionForm={setSubscriptionForm}
          createSubscription={createSubscription}
          wallets={wallets}
          subscriptionSuggestions={subscriptionSuggestions}
          subscriptions={subscriptions}
          toggleSubscription={toggleSubscription}
          removeSubscription={removeSubscription}
          formatCurrency={formatCurrency}
        />
      )}

      {activeTab === "investments" && (
        <InvestmentsTab
          investmentCreateForm={investmentCreateForm}
          setInvestmentCreateForm={setInvestmentCreateForm}
          createInvestment={createInvestment}
          investmentUpdateForm={investmentUpdateForm}
          setInvestmentUpdateForm={setInvestmentUpdateForm}
          updateInvestment={updateInvestment}
          investmentSellForm={investmentSellForm}
          setInvestmentSellForm={setInvestmentSellForm}
          sellInvestment={sellInvestment}
          wallets={wallets}
          investmentOutcome={investmentOutcome}
        />
      )}

      {activeTab === "debts" && (
        <DebtsTab
          debtForm={debtForm}
          setDebtForm={setDebtForm}
          createDebt={createDebt}
          repayForm={repayForm}
          setRepayForm={setRepayForm}
          repayDebt={repayDebt}
          wallets={wallets}
          debts={debts}
          formatCurrency={formatCurrency}
        />
      )}

      {activeTab === "assistant" && (
        <AssistantTab
          aiParseText={aiParseText}
          setAiParseText={setAiParseText}
          parseAiText={parseAiText}
          aiParseResult={aiParseResult}
          wallets={wallets}
          setOcrFile={setOcrFile}
          ocrWalletId={ocrWalletId}
          setOcrWalletId={setOcrWalletId}
          scanOcr={scanOcr}
          ocrResult={ocrResult}
          chatMessage={chatMessage}
          setChatMessage={setChatMessage}
          askChatbot={askChatbot}
          chatLoading={chatLoading}
          loadChatHistory={loadChatHistory}
          chatSessionId={chatSessionId}
          chatReply={chatReply}
          chatChartData={chatChartData}
          chatHistory={chatHistory}
        />
      )}
    </div>
  );
}

export default DashboardPage;
