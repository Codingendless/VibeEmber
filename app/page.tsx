"use client";

import {
  ArrowRight,
  Bell,
  Bookmark,
  Check,
  ChevronRight,
  CircleHelp,
  Clock3,
  Flame,
  Globe2,
  Heart,
  LayoutGrid,
  MessageCircle,
  Plus,
  Rocket,
  Search,
  Send,
  Sparkles,
  Star,
  Target,
  Users,
  X,
  Zap,
} from "lucide-react";
import { FormEvent, useMemo, useState } from "react";

type Project = {
  id: number;
  name: string;
  tagline: string;
  category: string;
  maker: string;
  avatar: string;
  icon: string;
  color: string;
  accent: string;
  votes: number;
  comments: number;
  badge?: string;
};

const projects: Project[] = [
  {
    id: 1,
    name: "流光简历",
    tagline: "把普通经历，变成会讲故事的作品集",
    category: "AI 工具",
    maker: "阿川",
    avatar: "川",
    icon: "光",
    color: "#171814",
    accent: "#dfff53",
    votes: 186,
    comments: 32,
    badge: "今日最热",
  },
  {
    id: 2,
    name: "饭搭子",
    tagline: "不再纠结吃什么，也找到一起吃的人",
    category: "微信小程序",
    maker: "林同学",
    avatar: "林",
    icon: "饭",
    color: "#ffdfd1",
    accent: "#ff6534",
    votes: 142,
    comments: 27,
    badge: "求体验",
  },
  {
    id: 3,
    name: "TabTab",
    tagline: "用 AI 把你的 100 个浏览器标签变成知识库",
    category: "浏览器插件",
    maker: "Jensen",
    avatar: "J",
    icon: "T",
    color: "#dce8ff",
    accent: "#3268ff",
    votes: 121,
    comments: 19,
  },
  {
    id: 4,
    name: "方言星球",
    tagline: "每天 3 分钟，学会一句家乡话",
    category: "教育",
    maker: "木棉",
    avatar: "棉",
    icon: "言",
    color: "#e1f3e9",
    accent: "#2c8958",
    votes: 96,
    comments: 14,
    badge: "首发",
  },
  {
    id: 5,
    name: "Billow",
    tagline: "自由职业者的极简记账与报价助手",
    category: "Web 应用",
    maker: "老麦",
    avatar: "麦",
    icon: "B",
    color: "#eee8ff",
    accent: "#7752d6",
    votes: 88,
    comments: 11,
  },
  {
    id: 6,
    name: "周末去哪",
    tagline: "给城市里不想做攻略的人一个答案",
    category: "生活方式",
    maker: "薇拉",
    avatar: "V",
    icon: "去",
    color: "#fff0bb",
    accent: "#df7516",
    votes: 76,
    comments: 16,
    badge: "征集反馈",
  },
];

const tasks = [
  { icon: "饭", color: "#ffdfd1", name: "饭搭子", title: "征集 30 位上海用户体验组队功能", progress: 76, current: 23, total: 30, reward: 20, time: "剩 2 天" },
  { icon: "T", color: "#dce8ff", name: "TabTab", title: "安装插件，完成 10 分钟真实体验", progress: 42, current: 21, total: 50, reward: 35, time: "剩 4 天" },
  { icon: "言", color: "#e1f3e9", name: "方言星球", title: "寻找 8 位广东话母语者校对内容", progress: 63, current: 5, total: 8, reward: 50, time: "剩 1 天" },
];

const categories = ["全部", "AI 工具", "微信小程序", "Web 应用", "移动 App", "教育", "生活方式"];

export default function Home() {
  const [category, setCategory] = useState("全部");
  const [search, setSearch] = useState("");
  const [voted, setVoted] = useState<number[]>([1]);
  const [joined, setJoined] = useState<number[]>([]);
  const [showSubmit, setShowSubmit] = useState(false);
  const [showSearch, setShowSearch] = useState(false);
  const [toast, setToast] = useState("");

  const visibleProjects = useMemo(() => {
    const q = search.trim().toLowerCase();
    return projects.filter((project) => {
      const categoryMatch = category === "全部" || project.category === category;
      const searchMatch = !q || `${project.name}${project.tagline}${project.category}`.toLowerCase().includes(q);
      return categoryMatch && searchMatch;
    });
  }, [category, search]);

  const notify = (message: string) => {
    setToast(message);
    window.setTimeout(() => setToast(""), 2400);
  };

  const toggleVote = (id: number) => {
    setVoted((items) => items.includes(id) ? items.filter((item) => item !== id) : [...items, id]);
  };

  const submitProject = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setShowSubmit(false);
    notify("提交成功，项目已进入审核队列 🚀");
  };

  return (
    <main>
      <header className="site-header">
        <a className="brand" href="#top" aria-label="起飞场首页">
          <span className="brand-mark"><Rocket size={19} strokeWidth={2.6} /></span>
          <span>起飞场</span>
          <small>LAUNCHDECK</small>
        </a>
        <nav className="desktop-nav" aria-label="主导航">
          <a className="active" href="#discover">发现产品</a>
          <a href="#help">互助大厅 <span className="nav-dot">12</span></a>
          <a href="#how">怎么玩</a>
        </nav>
        <div className="header-actions">
          <button className="icon-button" aria-label="搜索" onClick={() => setShowSearch(!showSearch)}><Search size={20} /></button>
          <button className="icon-button notification" aria-label="通知"><Bell size={20} /><i /></button>
          <button className="submit-button" onClick={() => setShowSubmit(true)}><Plus size={17} /> 发布项目</button>
          <button className="avatar-button" aria-label="个人中心">我</button>
        </div>
        {showSearch && (
          <div className="header-search">
            <Search size={18} />
            <input autoFocus value={search} onChange={(event) => setSearch(event.target.value)} placeholder="搜索产品、功能或赛道…" />
            <button onClick={() => { setShowSearch(false); setSearch(""); }} aria-label="关闭搜索"><X size={17} /></button>
          </div>
        )}
      </header>

      <section className="hero" id="top">
        <div className="hero-copy">
          <div className="eyebrow"><Sparkles size={15} /> 为 Vibe Coder 而生的产品首发社区</div>
          <h1>好产品，<br /><em>不该从 0 个用户</em>开始。</h1>
          <p>发布你的作品，换取真实体验和有用反馈。<br className="desktop-only" />先一起跨过冷启动，然后各凭本事起飞。</p>
          <div className="hero-actions">
            <button className="primary-button" onClick={() => setShowSubmit(true)}>发布我的产品 <ArrowRight size={18} /></button>
            <a className="text-button" href="#help">先帮别人一把 <ChevronRight size={17} /></a>
          </div>
          <div className="hero-proof">
            <div className="avatar-stack"><span>林</span><span>J</span><span>麦</span><span>V</span></div>
            <strong>2,086</strong><span>位独立开发者已入场</span>
          </div>
        </div>

        <div className="hero-board" aria-label="社区实时动态">
          <div className="board-top"><span><i /> 起飞场实况</span><small>LIVE</small></div>
          <div className="orbit orbit-one" />
          <div className="orbit orbit-two" />
          <div className="center-rocket"><Rocket size={33} /><span>正在起飞</span></div>
          <article className="float-card card-a"><span className="mini-icon coral">饭</span><div><b>饭搭子</b><small>获得 6 位新用户</small></div><em>+6</em></article>
          <article className="float-card card-b"><span className="mini-icon blue">T</span><div><b>TabTab</b><small>收到新反馈</small></div><MessageCircle size={17} /></article>
          <article className="float-card card-c"><span className="mini-icon green">言</span><div><b>方言星球</b><small>达成里程碑</small></div><Check size={16} /></article>
          <div className="spark spark-a">✦</div><div className="spark spark-b">✦</div><div className="spark spark-c">·</div>
          <div className="board-stats"><div><b>168</b><span>本周新作品</span></div><div><b>3,429</b><span>真实体验</span></div></div>
        </div>
      </section>

      <section className="ticker" aria-label="最新社区动态">
        <span className="ticker-title"><Zap size={14} fill="currentColor" /> 刚刚发生</span>
        <p><b>@鱼丸</b> 帮「方言星球」完成了内容校对</p><i />
        <p><b>「流光简历」</b> 达成 100 位真实用户</p>
        <a href="#help">查看动态 <ArrowRight size={15} /></a>
      </section>

      <section className="discover section-wrap" id="discover">
        <div className="section-heading">
          <div><span className="section-kicker"><Flame size={16} /> 正在发生</span><h2>这些产品，刚刚来到世界</h2></div>
          <a href="#all">查看全部 <ArrowRight size={17} /></a>
        </div>
        <div className="category-row" role="tablist" aria-label="产品分类">
          {categories.map((item) => <button key={item} className={category === item ? "selected" : ""} onClick={() => setCategory(item)}>{item}</button>)}
        </div>

        <div className="project-layout">
          <div className="project-grid">
            {visibleProjects.map((project, index) => (
              <article className="project-card" key={project.id} style={{ "--delay": `${index * 45}ms` } as React.CSSProperties}>
                <div className="project-visual" style={{ background: project.color }}>
                  <span className="project-number">0{index + 1}</span>
                  {project.badge && <span className="project-badge">{project.badge}</span>}
                  <div className="visual-rings" />
                  <div className="app-icon" style={{ background: project.accent, color: project.id === 1 ? "#171814" : "#fff" }}>{project.icon}</div>
                  <span className="visual-caption">MADE WITH VIBE</span>
                </div>
                <div className="project-info">
                  <div className="project-title-line"><div><h3>{project.name}</h3><span>{project.category}</span></div><button className={voted.includes(project.id) ? "vote voted" : "vote"} onClick={() => toggleVote(project.id)} aria-label={`为${project.name}点赞`}><Heart size={17} fill={voted.includes(project.id) ? "currentColor" : "none"} /> {project.votes + (voted.includes(project.id) && project.id !== 1 ? 1 : 0)}</button></div>
                  <p>{project.tagline}</p>
                  <div className="project-meta"><span className="maker-avatar">{project.avatar}</span><span>{project.maker}</span><span className="meta-spacer" /><MessageCircle size={15} /><span>{project.comments}</span><Bookmark size={15} /></div>
                </div>
              </article>
            ))}
            {visibleProjects.length === 0 && <div className="empty-state"><Search size={28} /><h3>还没有匹配的产品</h3><p>换个词试试，或者做第一个发布它的人。</p></div>}
          </div>

          <aside className="sidebar">
            <div className="side-card contribution-card">
              <span className="section-kicker"><Star size={15} /> 本周贡献榜</span>
              <h3>先伸手的人，值得被看见</h3>
              <ol>
                {[["鱼丸", "产品经理", "428", "🐟"], ["阿耀", "全栈开发", "386", "🌞"], ["Nora", "独立设计师", "342", "N"], ["小杰", "Vibe Coder", "296", "杰"]].map((user, index) => (
                  <li key={user[0]}><span className={`rank rank-${index + 1}`}>{index + 1}</span><span className="leader-avatar">{user[3]}</span><div><b>{user[0]}</b><small>{user[1]}</small></div><strong>{user[2]} <i>pts</i></strong></li>
                ))}
              </ol>
              <button onClick={() => notify("已打开完整贡献榜") }>查看完整榜单 <ChevronRight size={16} /></button>
            </div>
            <div className="side-card idea-card">
              <div className="idea-icon"><CircleHelp size={23} /></div>
              <div><span>开做之前，先搜一搜</span><h3>别再重复造轮子</h3><p>搜索 680+ 个真实产品和用户反馈，找到还没被解决的问题。</p><button onClick={() => { setShowSearch(true); window.scrollTo({ top: 0, behavior: "smooth" }); }}>查看赛道地图 <ArrowRight size={16} /></button></div>
            </div>
          </aside>
        </div>
      </section>

      <section className="help-section" id="help">
        <div className="section-wrap">
          <div className="section-heading light">
            <div><span className="section-kicker"><Users size={16} /> 互助大厅</span><h2>今天帮一把，明天有人推你一程</h2><p>完成真实体验任务获得火苗，用火苗发起自己的冷启动计划。</p></div>
            <div className="flame-balance"><span><Flame size={18} fill="currentColor" /> 我的火苗</span><strong>120</strong><button onClick={() => notify("快去完成一个体验任务吧")}>+赚火苗</button></div>
          </div>
          <div className="task-list">
            {tasks.map((task, index) => (
              <article className="task-card" key={task.name}>
                <div className="task-icon" style={{ background: task.color }}>{task.icon}</div>
                <div className="task-main"><div className="task-name"><b>{task.name}</b><span>真实体验</span></div><h3>{task.title}</h3><div className="progress-row"><div className="progress-track"><i style={{ width: `${task.progress}%` }} /></div><span>{task.current}/{task.total} 人</span></div></div>
                <div className="task-time"><Clock3 size={15} />{task.time}</div>
                <div className="reward"><Flame size={15} fill="currentColor" /> +{task.reward}</div>
                <button className={joined.includes(index) ? "joined" : ""} onClick={() => { setJoined((all) => all.includes(index) ? all : [...all, index]); notify(joined.includes(index) ? "你已经领取过这个任务" : "任务已领取，去产品页完成体验吧"); }}>{joined.includes(index) ? <><Check size={16} /> 已领取</> : <>去帮忙 <ArrowRight size={16} /></>}</button>
              </article>
            ))}
          </div>
          <div className="help-footer"><span><Target size={17} /> 所有任务都要求真实体验与有效反馈，拒绝机器刷量。</span><a href="#all-tasks">浏览全部 36 个任务 <ArrowRight size={16} /></a></div>
        </div>
      </section>

      <section className="how-section section-wrap" id="how">
        <span className="section-kicker"><LayoutGrid size={16} /> 就这么简单</span>
        <h2>别让你的下一个好产品，<br />死在没人知道。</h2>
        <div className="steps">
          <div><span>01</span><div className="step-icon"><Send size={23} /></div><h3>发布作品</h3><p>用 3 分钟讲清你做了什么，为谁解决什么问题。</p></div>
          <div><span>02</span><div className="step-icon"><Users size={23} /></div><h3>贡献真实体验</h3><p>试用别人的产品，给出有价值的反馈，积累火苗。</p></div>
          <div><span>03</span><div className="step-icon lime"><Rocket size={23} /></div><h3>发起冷启动</h3><p>换取首批真实用户与反馈，剩下的靠产品起飞。</p></div>
        </div>
      </section>

      <footer>
        <div className="footer-brand"><span className="brand-mark"><Rocket size={19} /></span><div><b>起飞场</b><small>让好产品被第一批人看见。</small></div></div>
        <div className="footer-links"><a href="#discover">发现</a><a href="#help">互助</a><a href="#how">社区公约</a><a href="mailto:hello@launchdeck.cn">联系我们</a></div>
        <span>© 2026 LaunchDeck</span>
      </footer>

      {showSubmit && (
        <div className="modal-backdrop" role="presentation" onMouseDown={() => setShowSubmit(false)}>
          <div className="submit-modal" role="dialog" aria-modal="true" aria-labelledby="submit-title" onMouseDown={(event) => event.stopPropagation()}>
            <button className="modal-close" onClick={() => setShowSubmit(false)} aria-label="关闭"><X size={19} /></button>
            <span className="modal-icon"><Rocket size={24} /></span>
            <span className="section-kicker">发布作品</span>
            <h2 id="submit-title">让你的产品被看见</h2>
            <p>不用写商业计划书，讲清它对谁有用就好。</p>
            <form onSubmit={submitProject}>
              <label>产品名称<input required placeholder="例如：饭搭子" /></label>
              <label>一句话介绍<input required placeholder="你帮用户解决了什么问题？" /></label>
              <div className="form-row"><label>产品链接<input type="url" required placeholder="https://" /></label><label>产品类型<select defaultValue=""><option value="" disabled>请选择</option><option>AI 工具</option><option>微信小程序</option><option>Web 应用</option><option>移动 App</option></select></label></div>
              <label>现在最需要的帮助<textarea placeholder="例如：希望 20 位用户体验组队功能并留下反馈…" /></label>
              <button className="primary-button" type="submit">提交审核 <ArrowRight size={17} /></button>
            </form>
          </div>
        </div>
      )}

      {toast && <div className="toast"><Check size={17} />{toast}</div>}
    </main>
  );
}
