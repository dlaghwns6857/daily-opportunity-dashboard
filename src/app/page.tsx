"use client";

import { useMemo, useState } from "react";
import postsData from "../../data/posts.json";

type DashboardItem = {
  id: string;
  category: "채용" | "지원금";
  subcategory: string;
  title: string;
  org: string;
  deadline: string;
  url: string;
  source: string;
  region: string;
  amount?: string;
  is_new: boolean;
};

type DashboardData = {
  updated_at: string;
  failed_sources?: FailedSourceLink[];
  items: DashboardItem[];
};

type FilterTab = "전체" | "채용" | "인턴" | "지원금";

type FailedSourceLink = {
  name: string;
  reason: string;
  url: string;
};

const dashboardData = postsData as DashboardData;

const tabs: FilterTab[] = ["전체", "채용", "인턴", "지원금"];

function formatUpdatedAt(value: string) {
  return new Intl.DateTimeFormat("ko-KR", {
    year: "numeric",
    month: "long",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit"
  }).format(new Date(value));
}

function getDaysUntil(deadline: string) {
  const today = new Date();
  const target = new Date(`${deadline}T23:59:59`);
  const startOfToday = new Date(today.getFullYear(), today.getMonth(), today.getDate());
  const difference = target.getTime() - startOfToday.getTime();

  return Math.ceil(difference / (1000 * 60 * 60 * 24));
}

function getCardTone(item: DashboardItem) {
  if (item.category === "지원금") {
    return {
      badge: "bg-emerald-100 text-emerald-700 dark:bg-emerald-500/15 dark:text-emerald-300",
      accent: "ring-emerald-200/80 dark:ring-emerald-500/20",
      dot: "bg-emerald-500"
    };
  }

  if (item.subcategory.includes("인턴")) {
    return {
      badge: "bg-violet-100 text-violet-700 dark:bg-violet-500/15 dark:text-violet-300",
      accent: "ring-violet-200/80 dark:ring-violet-500/20",
      dot: "bg-violet-500"
    };
  }

  return {
    badge: "bg-sky-100 text-sky-700 dark:bg-sky-500/15 dark:text-sky-300",
    accent: "ring-sky-200/80 dark:ring-sky-500/20",
    dot: "bg-sky-500"
  };
}

export default function HomePage() {
  const [activeTab, setActiveTab] = useState<FilterTab>("전체");
  const [searchQuery, setSearchQuery] = useState("");
  const failedSourceLinks = dashboardData.failed_sources ?? [];

  const filteredItems = useMemo(() => {
    const normalizedQuery = searchQuery.trim().toLowerCase();

    const tabFilteredItems = (() => {
      switch (activeTab) {
        case "채용":
          return dashboardData.items.filter(
            (item) => item.category === "채용" && item.subcategory !== "인턴"
          );
        case "인턴":
          return dashboardData.items.filter((item) => item.subcategory === "인턴");
        case "지원금":
          return dashboardData.items.filter((item) => item.category === "지원금");
        default:
          return dashboardData.items;
      }
    })();

    if (!normalizedQuery) {
      return tabFilteredItems;
    }

    return tabFilteredItems.filter((item) => {
      const title = item.title.toLowerCase();
      const org = item.org.toLowerCase();

      return title.includes(normalizedQuery) || org.includes(normalizedQuery);
    });
  }, [activeTab, searchQuery]);

  return (
    <main className="mx-auto flex min-h-screen w-full max-w-7xl flex-col px-4 py-6 sm:px-6 lg:px-8">
      <section className="rounded-[28px] border border-white/60 bg-white/80 p-5 shadow-panel backdrop-blur-xl dark:border-slate-800 dark:bg-slate-950/80 sm:p-8">
        <div className="flex flex-col gap-6">
          <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
            <div className="space-y-3">
              <span className="inline-flex w-fit items-center rounded-full bg-slate-900 px-3 py-1 text-xs font-semibold text-white dark:bg-slate-100 dark:text-slate-900">
                Daily Personal Dashboard
              </span>
              <div className="space-y-2">
                <h1 className="font-[var(--font-manrope)] text-3xl font-extrabold tracking-tight text-slate-900 dark:text-slate-50 sm:text-4xl">
                  공기업 채용 · 인턴 · 청년 지원금
                </h1>
                <p className="max-w-2xl text-sm leading-6 text-slate-600 dark:text-slate-300 sm:text-base">
                  매일 아침 자동 수집된 공고를 한 화면에서 빠르게 확인할 수 있는 개인용 정보 대시보드입니다.
                </p>
              </div>
            </div>

            <div className="rounded-2xl border border-slate-200 bg-slate-50/90 px-4 py-3 text-sm text-slate-600 dark:border-slate-800 dark:bg-slate-900/70 dark:text-slate-300">
              <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-400 dark:text-slate-500">
                Last Updated
              </p>
              <p className="mt-1 font-semibold text-slate-900 dark:text-slate-100">
                {formatUpdatedAt(dashboardData.updated_at)}
              </p>
            </div>
          </div>

          <div className="flex flex-wrap gap-2">
            {tabs.map((tab) => {
              const isActive = tab === activeTab;

              return (
                <button
                  key={tab}
                  type="button"
                  onClick={() => setActiveTab(tab)}
                  className={`rounded-full px-4 py-2 text-sm font-semibold transition ${
                    isActive
                      ? "bg-slate-900 text-white shadow-lg shadow-slate-900/10 dark:bg-slate-100 dark:text-slate-950"
                      : "border border-slate-200 bg-white text-slate-600 hover:border-slate-300 hover:text-slate-900 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-300 dark:hover:border-slate-700 dark:hover:text-slate-100"
                  }`}
                >
                  {tab}
                </button>
              );
            })}
          </div>

          <div className="max-w-xl">
            <label className="sr-only" htmlFor="dashboard-search">
              공고명, 기관명 검색
            </label>
            <input
              id="dashboard-search"
              type="search"
              value={searchQuery}
              onChange={(event) => setSearchQuery(event.target.value)}
              placeholder="공고명, 기관명 검색..."
              className="w-full rounded-2xl border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 outline-none transition placeholder:text-slate-400 focus:border-slate-400 focus:ring-4 focus:ring-slate-200/70 dark:border-slate-800 dark:bg-slate-900 dark:text-slate-100 dark:placeholder:text-slate-500 dark:focus:border-slate-600 dark:focus:ring-slate-800"
            />
          </div>
        </div>
      </section>

      <section className="mt-6 grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {filteredItems.map((item) => {
          const tone = getCardTone(item);
          const daysUntil = getDaysUntil(item.deadline);
          const isDeadlineSoon = daysUntil >= 0 && daysUntil <= 7;

          return (
            <a
              key={item.id}
              href={item.url}
              target="_blank"
              rel="noreferrer"
              className={`group rounded-[24px] border border-slate-200 bg-white/85 p-5 shadow-sm ring-1 transition hover:-translate-y-1 hover:shadow-panel dark:border-slate-800 dark:bg-slate-950/75 ${tone.accent}`}
            >
              <div className="flex items-start justify-between gap-3">
                <div className="flex flex-wrap items-center gap-2">
                  <span className={`inline-flex items-center rounded-full px-2.5 py-1 text-xs font-semibold ${tone.badge}`}>
                    {item.subcategory.includes("인턴") ? "인턴" : item.category}
                  </span>
                  {item.is_new ? (
                    <span className="inline-flex items-center rounded-full bg-rose-100 px-2.5 py-1 text-xs font-bold text-rose-700 dark:bg-rose-500/15 dark:text-rose-300">
                      NEW
                    </span>
                  ) : null}
                  {item.region === "부산" ? (
                    <span className="inline-flex items-center rounded-full bg-amber-100 px-2.5 py-1 text-xs font-semibold text-amber-700 dark:bg-amber-500/15 dark:text-amber-300">
                      📍 부산
                    </span>
                  ) : null}
                </div>
                <span className={`mt-1 h-2.5 w-2.5 flex-none rounded-full ${tone.dot}`} />
              </div>

              <div className="mt-4 space-y-3">
                <div>
                  <h2 className="text-lg font-bold leading-7 text-slate-900 transition group-hover:text-slate-700 dark:text-slate-50 dark:group-hover:text-slate-200">
                    {item.title}
                  </h2>
                  <p className="mt-2 text-sm font-medium text-slate-700 dark:text-slate-200">{item.org}</p>
                </div>

                <div className="grid gap-2 text-sm text-slate-600 dark:text-slate-300">
                  <p>
                    <span className="font-semibold text-slate-900 dark:text-slate-100">출처</span> · {item.source}
                  </p>
                  <p className={isDeadlineSoon ? "font-semibold text-rose-600 dark:text-rose-300" : ""}>
                    <span className="font-semibold text-slate-900 dark:text-slate-100">마감일</span> · {item.deadline}
                    {isDeadlineSoon ? ` · ${daysUntil}일 남음` : ""}
                  </p>
                  <p>
                    <span className="font-semibold text-slate-900 dark:text-slate-100">지역</span> · {item.region}
                  </p>
                  {item.amount ? (
                    <p>
                      <span className="font-semibold text-slate-900 dark:text-slate-100">지원금</span> · {item.amount}
                    </p>
                  ) : null}
                </div>
              </div>
            </a>
          );
        })}
      </section>

      {failedSourceLinks.length > 0 ? (
        <section className="mt-8 rounded-[28px] border border-amber-200 bg-amber-50/80 p-5 shadow-sm backdrop-blur-xl dark:border-amber-500/20 dark:bg-amber-500/10 sm:p-8">
          <div className="flex flex-col gap-4">
            <div className="space-y-2">
              <span className="inline-flex w-fit items-center rounded-full bg-amber-600 px-3 py-1 text-xs font-semibold text-white dark:bg-amber-400 dark:text-slate-950">
                점검 필요 Source
              </span>
              <h2 className="font-[var(--font-manrope)] text-2xl font-extrabold tracking-tight text-slate-900 dark:text-slate-50">
                실패 항목 원문 링크
              </h2>
              <p className="text-sm leading-6 text-slate-700 dark:text-slate-300">
                최근 실행에서 비어 있거나 실패한 사이트는 원문 페이지를 바로 열 수 있게 표시합니다.
              </p>
            </div>

            <div className="grid gap-3 md:grid-cols-2">
              {failedSourceLinks.map((source) => (
                <a
                  key={source.name}
                  href={source.url}
                  target="_blank"
                  rel="noreferrer"
                  className="rounded-[20px] border border-amber-200 bg-white/90 p-4 transition hover:-translate-y-0.5 hover:shadow-md dark:border-amber-500/20 dark:bg-slate-950/70"
                >
                  <div className="flex items-center justify-between gap-3">
                    <h3 className="text-base font-bold text-slate-900 dark:text-slate-100">{source.name}</h3>
                    <span className="rounded-full bg-amber-100 px-2.5 py-1 text-xs font-semibold text-amber-700 dark:bg-amber-500/15 dark:text-amber-300">
                      바로가기
                    </span>
                  </div>
                  <p className="mt-2 text-sm leading-6 text-slate-600 dark:text-slate-300">{source.reason}</p>
                  <p className="mt-3 text-xs font-medium text-slate-500 dark:text-slate-400">{source.url}</p>
                </a>
              ))}
            </div>
          </div>
        </section>
      ) : null}
    </main>
  );
}