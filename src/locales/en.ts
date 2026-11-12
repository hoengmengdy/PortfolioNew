import type { ProjectCopy, ProjectFilter, ProjectSlug, SkillCategoryId } from '../types';

/** Keeps `note` and `unverified` optional on every project, and requires every slug. */
const defineProjects = (items: Record<ProjectSlug, ProjectCopy>) => items;

export const en = {
  meta: {
    title: 'Hoeng Mengdy | Full-Stack Developer in Phnom Penh',
    description:
      'Hoeng Mengdy is a full-stack developer and BIT student in Phnom Penh, Cambodia, building modern web applications and practical digital solutions.',
    notFoundTitle: 'Page not found | Hoeng Mengdy',
  },
  common: {
    name: 'Hoeng Mengdy',
    brand: 'Building Digital Experiences. Creating Real Solutions.',
    skipToContent: 'Skip to main content',
    loading: 'Loading',
    externalLink: 'opens in a new tab',
    close: 'Close',
  },
  nav: {
    label: 'Main navigation',
    home: 'Home',
    about: 'About',
    skills: 'Skills',
    projects: 'Projects',
    education: 'Education',
    services: 'Services',
    contact: 'Contact',
    openMenu: 'Open menu',
    closeMenu: 'Close menu',
    downloadCv: 'Download CV',
    requestCv: 'Request CV',
    switchLanguage: 'Language',
    themeToDark: 'Switch to dark theme',
    themeToLight: 'Switch to light theme',
    backToTop: 'Back to top',
  },
  hero: {
    available: 'Available for opportunities',
    badge: 'Full-Stack Developer · Phnom Penh',
    titleLine1: 'Turning Ideas Into',
    titleLine2: 'Digital Experiences.',
    description:
      "I'm Hoeng Mengdy, a developer in Phnom Penh who builds modern web applications and practical digital solutions, from the first database table to the final interface.",
    explore: 'Explore My Work',
    downloadCv: 'Download My CV',
    requestCv: 'Request My CV',
    contact: 'Contact Me',
    roles: ['Full-Stack Developer', 'Software Developer', 'BIT Student'],
    portraitAlt: 'Portrait of Hoeng Mengdy',
    monogramAlt: 'HM monogram of Hoeng Mengdy',
  },
  about: {
    eyebrow: 'About',
    title: 'About Me',
    bio: "Hi, I'm Hoeng Mengdy, a passionate Software Developer and Information Technology student. I specialize in building modern web applications, intelligent systems, and scalable digital solutions. I enjoy transforming ideas into functional products through clean code, thoughtful design, and innovative technologies.",
    educationLabel: 'Education',
    educationValue: 'Bachelor of Information Technology (BIT), BELTEI International University',
    locationLabel: 'Based in',
    locationValue: 'Phnom Penh, Cambodia',
    goalLabel: 'My goal',
    goalValue:
      'To create digital solutions that are high quality, efficient, and able to solve real problems in everyday life.',
    passionLabel: 'What drives me',
    passionValue:
      'Curiosity about new technology, and the moment an idea becomes something people can actually use.',
    interestsLabel: 'Development interests',
    interests: [
      'Full-Stack Web Development',
      'Artificial Intelligence',
      'Software Engineering',
      'Cybersecurity',
      'Database Architecture',
      'Digital Innovation',
    ],
  },
  skills: {
    eyebrow: 'Skills',
    title: 'Technical Skills',
    lead: 'The tools I reach for across the stack, from interface to infrastructure.',
    filterLabel: 'Filter skills by category',
    all: 'All',
    categories: {
      frontend: 'Frontend',
      backend: 'Backend',
      database: 'Database',
      tools: 'Tools & Platforms',
    } satisfies Record<SkillCategoryId, string>,
  },
  projects: {
    eyebrow: 'Projects',
    title: 'Featured Projects',
    lead: 'Real projects, described by what the code actually does. Where something still depends on a third party, it says so.',
    filterLabel: 'Filter projects by technology',
    all: 'All',
    filters: {
      react: 'React',
      vue: 'Vue',
      flask: 'Flask',
      node: 'Node.js',
      telegram: 'Telegram',
      web: 'HTML/CSS/JS',
    } satisfies Record<ProjectFilter, string>,
    featured: 'Featured',
    viewDetails: 'View Details',
    sourceCode: 'GitHub',
    liveDemo: 'Live Demo',
    resultCount: (count: number) => `${count} ${count === 1 ? 'project' : 'projects'} shown`,
    keyFeatures: 'Main features',
    unverifiedTitle: 'Built, not yet verified live',
    pendingFeatures:
      'Features will be listed here once they are confirmed against the source code.',
    technologies: 'Technologies',
    links: 'Links',
    noLinks: 'No public link is available for this project yet.',
    screenshot: 'Screenshot',
    illustration: 'Illustration',
    previous: 'Previous project',
    next: 'Next project',
    items: defineProjects({
      'lsv-lucky-spin': {
        title: 'LSV Lucky Spin',
        category: 'Promotional web app',
        summary:
          'A mobile-first prize wheel for LSV Industry: customers scan a QR code, spin once, and win a product.',
        description:
          'A lucky-spin promotion page built for LSV Industry customers. The wheel is drawn on a high-resolution canvas with a product photo in every slice and the LSV logo at its centre. Each prize has its own win chance, so the business decides the odds, and a prize can stay on the wheel while being set so it is never won. After one spin, a Bootstrap modal shows the prize with its photo.',
        features: [
          'Prize wheel drawn on canvas, sharp on phone screens',
          'Weighted odds set per prize, including display-only prizes',
          'One spin per visit, with a smooth five-second spin animation',
          'Winner pop-up with the prize name and product photo',
          'Responsive Bootstrap 5 layout with Khmer Kantumruy Pro font',
        ],
        coverAlt:
          'The LSV Lucky Spin page: a green prize wheel with product photos and a SPIN button',
      },
      workday: {
        title: 'Employee Task Management & Daily Reporting System',
        category: 'Full-stack web application',
        summary:
          'A role-based workspace where managers assign tasks, employees report their work every day, and reviews happen in one place.',
        description:
          'A web-based employee management and daily reporting platform designed to improve task assignment, productivity tracking, and work reporting. Each role has its own workflow: a super admin sets up departments and accounts, managers create and review tasks, and employees update progress and submit daily reports. The interface works in both Khmer and English.',
        features: [
          'Employee, department, and role management',
          'Task assignment with progress tracking',
          'Daily reports with Save Draft and Submit',
          'Approval center with revision requests and feedback',
          'Recurring daily tasks that cannot create duplicates',
          'Telegram notifications for new task assignments',
          'Admin dashboards, filtered analytics, and report export',
          'Khmer and English interface with a dark theme',
        ],
        coverAlt: 'The new task form in the Workday application, with a repeat daily option',
      },
      empress: {
        title: 'Empress',
        category: 'E-commerce web application',
        summary:
          'A bilingual skincare shop built for Cambodia, with Khmer addresses, local payment flows, Telegram sign-in, and a full admin dashboard.',
        description:
          'A modern web application focused on creating a professional digital experience for a skincare brand concept. Customers can browse products, check out with a Cambodian delivery address, and follow their order through a private link. Administrators manage orders, products, messages, and retailer listings from one dashboard.',
        features: [
          'Product shop, cart, and checkout',
          'Full Khmer and English translations',
          'Province, district, and commune address picker for Cambodia',
          'Private order links showing status and payment instructions',
          'ABA PayWay and bank transfer payment flows',
          'Customer sign-in with a one-time code sent through Telegram',
          'Admin dashboard for orders, products, messages, and retailers',
          'CSRF protection and rate-limited login',
        ],
        note: 'Payment methods turn on only after merchant credentials are configured.',
        coverAlt: 'The Empress home page, with a skincare headline beside a sky and hills scene',
      },
      bcommunity: {
        title: 'Bcommunity',
        category: 'Community platform',
        summary:
          'A members-only community platform for connecting, learning, and sharing, with posts, Q&A, mentorship, and direct messages.',
        description:
          'A full-stack community platform with a Vue frontend and a Flask API. Members sign in to an existing account, follow community posts, ask questions, and message each other, while administrators get an overview and manage users.',
        features: [
          'Community feed with posts and post details',
          'Q&A, code review, knowledge base, mentorship, and leaderboard pages',
          'Direct messages with replies, reactions, and edits',
          'Member profiles with profile photos',
          'Admin overview and user management',
          'Signed sessions that the server can revoke',
          'Push notification subscriptions',
        ],
        note: 'Public sign-up is turned off, so visitors without an account will only see the sign-in page on the live site.',
        coverAlt: 'Illustration of connected community members in gold on a dark background',
      },
      'lsv-industry': {
        title: 'LSV Industry Online Store',
        category: 'E-commerce web application',
        summary:
          'A live online store for LSV Industry products, with customer accounts, a cart and checkout, and an admin dashboard.',
        description:
          'A complete Flask e-commerce application that brings the OKA, RINs, Empress, and NaturePlus brands into one catalog. Customers can search and filter products, save favorites, check out, and review past orders, while administrators manage products, orders, and users.',
        features: [
          'Product catalog with search and brand filters',
          'Product detail pages',
          'Customer accounts with profile and order history',
          'Wishlist',
          'Shopping cart and checkout with delivery addresses',
          'Admin dashboard for products, categories, orders, and users',
          'Khmer and English interface',
          'SQLite for development and PostgreSQL for production',
        ],
        coverAlt: 'The LSV Industry store home page, with a product banner and four brand links',
      },
      'smm-digital': {
        title: 'SMM Digital',
        category: 'Marketplace website',
        summary:
          'A data-driven marketplace storefront for digital products, with category filters, search, Telegram contact, and a Flask admin panel.',
        description:
          'A responsive marketplace website that lists Facebook Pages and related digital services. The storefront loads its products from a JSON API, and an administrator manages the listings and their images from a protected Flask panel.',
        features: [
          'Responsive storefront with category filters and search',
          'Listings with price, discount, and follower information',
          'Protected admin login',
          'Admin tools to add, edit, and delete products and upload images',
          'JSON API for products',
          'Product data and images stored in private Vercel Blob storage',
          'Direct contact through Telegram',
        ],
        coverAlt:
          'The SMM Digital home page, with a Facebook Pages headline on a dark and gold design',
      },
      qrpage: {
        title: 'QRpage',
        category: 'Landing page',
        summary:
          'A responsive QR landing page that takes visitors straight to two Facebook Pages, by scan or by tap.',
        description:
          'A QR code web page that connects visitors to two Facebook Pages. Each card shows a scannable QR code generated from that card’s own link, so the code and the button always point to the same place.',
        features: [
          'Scannable QR code and direct link for each Page',
          'QR codes generated from each button’s destination',
          'PNG fallback that still works with JavaScript turned off',
          'Fonts and QR assets served locally',
          'Responsive layout for phone and desktop',
        ],
        coverAlt: 'The QRpage landing page with two cards, each showing a QR code',
      },
    }),
  },
  education: {
    eyebrow: 'Education',
    title: 'Education',
    degree: 'Bachelor of Information Technology (BIT)',
    university: 'BELTEI International University',
    degreeBody:
      'I study information technology as the foundation of my work, connecting what I learn in class with software I build myself.',
    interestsTitle: 'Academic interests',
    interestsBody:
      'Software engineering, database architecture, artificial intelligence, and cybersecurity are the areas I most want to deepen.',
    journeyTitle: 'Learning through building',
    journeyBody:
      'Alongside my degree, I learn by shipping real projects. Each one teaches me something new about how software works beyond the classroom.',
  },
  services: {
    eyebrow: 'Services',
    title: 'What I Can Build',
    lead: 'The kinds of work I can take on, based on the skills and projects shown on this site.',
    items: [
      {
        title: 'Website Development',
        description: 'Fast, responsive websites that present your work clearly on any device.',
      },
      {
        title: 'Frontend Development',
        description: 'Accessible React and TypeScript interfaces built from reusable components.',
      },
      {
        title: 'Backend Development',
        description:
          'Server applications in Flask, Laravel, or Node.js with validation and access control.',
      },
      {
        title: 'Full-Stack Application Development',
        description:
          'Complete applications, from the data model and API to the finished interface.',
      },
      {
        title: 'Database Design',
        description:
          'Clear relational schemas in MySQL or PostgreSQL that stay reliable as data grows.',
      },
      {
        title: 'REST API Integration',
        description:
          'Connecting your product to third-party services, or building an API of your own.',
      },
      {
        title: 'Dashboard Development',
        description: 'Admin panels and analytics views that turn your data into clear decisions.',
      },
      {
        title: 'System Development',
        description: 'Internal tools with roles, workflows, and reports that fit how a team works.',
      },
    ],
  },
  pages: {
    eyebrow: 'Facebook Pages',
    title: 'Pages I Manage',
    lead: 'I run these Facebook Pages day to day: creating posts, replying to messages, and promoting content.',
    managedLabel: 'Pages managed',
    role: 'Admin',
    viewPage: 'View Page',
    showAll: 'Show all Pages',
    showLess: 'Show fewer',
    tasks: ['Create posts', 'Reply to messages', 'Promote posts', 'Track notifications'],
  },
  journey: {
    eyebrow: 'My Journey',
    title: 'How I Got Here',
    lead: 'Not a list of job titles. These are the stages that have shaped how I build software.',
    seeWork: 'Related work',
    chapters: [
      {
        title: 'Learning programming',
        body: 'It started with the fundamentals: HTML, CSS, JavaScript, and learning how to think through a problem in code.',
        projects: [],
      },
      {
        title: 'Building practical projects',
        body: 'I moved quickly from exercises to small tools that real people could use, because finishing something teaches more than following along.',
        projects: ['qrpage'],
      },
      {
        title: 'Exploring web technologies',
        body: 'Working with Flask, Laravel, Node.js, and React showed me how the different layers of the web fit together.',
        projects: [],
      },
      {
        title: 'Developing full-stack applications',
        body: 'Next came complete systems, with authentication, roles, databases, and integrations with services like Telegram and ABA PayWay.',
        projects: ['workday', 'empress'],
      },
      {
        title: 'Improving software engineering skills',
        body: 'Now I focus on what makes software last: automated tests, security, clean structure, and being honest about what is finished and what is not.',
        projects: [],
      },
    ] satisfies Array<{ title: string; body: string; projects: ProjectSlug[] }>,
  },
  contact: {
    eyebrow: 'Contact',
    title: "Let's Build Something Real",
    lead: 'Have a project, a question, or an idea? Message me on Telegram.',
    location: 'Phnom Penh, Cambodia',
  },
  footer: {
    intro:
      'Software developer and Information Technology student building modern web applications in Phnom Penh, Cambodia.',
    navigate: 'Navigate',
    connect: 'Connect',
    rights: 'Hoeng Mengdy. All rights reserved.',
    builtWith: 'Built with React & TypeScript.',
  },
  notFound: {
    eyebrow: 'Error 404',
    title: 'This page could not be found.',
    body: 'The link may be old, or the page may have moved.',
    home: 'Back to home',
  },
};

export type Dictionary = typeof en;
