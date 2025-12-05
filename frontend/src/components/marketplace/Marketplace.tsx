import React, { useState } from 'react';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Badge } from '../ui/badge';
import { Card } from '../ui/card';
import { ScrollArea } from '../ui/scroll-area';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '../ui/dialog';
import {
  Search,
  Zap,
  Brain,
  Wrench,
  Heart,
  Footprints,
  Shield,
  Download,
  Star,
  Sparkles,
  MessageSquare,
  FileSearch,
  Mail,
  Calendar,
  DollarSign,
  Code,
  BarChart,
} from 'lucide-react';
import { AgentConfiguration, NodeInstance } from '../../types/agent-parts';
import { toast } from 'sonner';
import { Footer } from '../Footer';
import { TopBar } from '../TopBar';

interface AgentBlueprint {
  id: string;
  name: string;
  description: string;
  category: 'Customer Support' | 'Data & Analytics' | 'Content Creation' | 'Productivity' | 'Sales & Marketing';
  icon: React.ReactNode;
  rating: number;
  downloads: number;
  featured: boolean;
  config: AgentConfiguration;
  tags: string[];
}

const createNode = (
  instanceId: string,
  id: string,
  name: string,
  type: NodeInstance['type'],
  color: string,
  category: string,
  config: Record<string, any>
): NodeInstance => ({
  instanceId,
  id,
  name,
  type,
  color,
  category,
  position: { x: 0, y: 0 },
  config,
});

const SAMPLE_BLUEPRINTS: AgentBlueprint[] = [
  {
    id: 'blueprint-agno-competitor',
    name: 'Competitor Intelligence Squad',
    description: 'Agno-powered team for assembling competitor dossiers with Tavily deep search and Firecrawl snapshots, mirroring the multi-agent setup in the Blueprint Guide.',
    category: 'Sales & Marketing',
    icon: <Sparkles className="w-5 h-5" />,
    rating: 4.9,
    downloads: 812,
    featured: true,
    tags: ['agno', 'team', 'research'],
    config: {
      head: createNode('head-ci', 'gpt4o-mini', 'Strategy Orchestrator', 'head', '#10a37f', 'Head', {
        model: 'gpt-4o-mini',
        temperature: 0.6,
        systemPrompt: 'You coordinate Agno research agents to compile competitive insights with citations.',
      }),
      arms: [
        createNode('arm-ci-1', 'tavily-search', 'Advanced Market Sweep', 'arm', '#3b82f6', 'Tool', {
          searchDepth: 'advanced',
          include_answer: true,
          maxResults: 8,
        }),
        createNode('arm-ci-2', 'http-tool', 'Firecrawl Snapshot Tool', 'arm', '#3b82f6', 'Tool', {
          baseUrl: 'https://api.firecrawl.dev',
          defaultHeaders: { Authorization: 'Bearer ${FIRECRAWL_KEY}' },
        }),
      ],
      heart: createNode('heart-ci', 'convo-memory', 'Competitor Memory', 'heart', '#ec4899', 'Memory', {
        maxMessages: 12,
        summaryThreshold: 9,
      }),
      leg: createNode('leg-ci', 'team', 'Agno Team Execution', 'leg', '#a855f7', 'Execution', {
        mode: 'team',
        coordinator: 'research-to-insight',
      }),
      spine: createNode('spine-ci', 'max-tool-calls', 'Signal Guard', 'spine', '#06b6d4', 'Guardrail', {
        maxCalls: 8,
        timeWindow: '2m',
      }),
      teamMembers: [
        {
          id: 'ci-scout',
          name: 'Market Scout',
          role: 'Harvest web signals and citations',
          head: createNode('head-ci-scout', 'gpt4o-mini', 'Scout Head', 'head', '#10a37f', 'Head', {
            temperature: 0.4,
            systemPrompt: 'Collect reliable competitor facts, highlight metrics, and cite URLs.',
          }),
          arms: [
            createNode('arm-ci-scout', 'tavily-search', 'Source Discovery', 'arm', '#3b82f6', 'Tool', {
              searchDepth: 'advanced',
              include_answer: false,
              maxResults: 6,
            }),
          ],
        },
        {
          id: 'ci-analyst',
          name: 'Insight Synthesizer',
          role: 'Summarize differentiators and risks',
          head: createNode('head-ci-analyst', 'gpt4o-mini', 'Analyst Head', 'head', '#10a37f', 'Head', {
            temperature: 0.5,
            systemPrompt: 'Transform findings into actionable battlecards and heat maps.',
          }),
          arms: [
            createNode('arm-ci-analyst', 'http-tool', 'Pricing Sheet Fetcher', 'arm', '#3b82f6', 'Tool', {
              baseUrl: 'https://api.firecrawl.dev',
            }),
          ],
          heart: createNode('heart-ci-analyst', 'convo-memory', 'Insight Scratchpad', 'heart', '#ec4899', 'Memory', {
            maxMessages: 6,
          }),
        },
      ],
    },
  },
  {
    id: 'blueprint-agno-startup',
    name: 'Startup Trend Radar',
    description: 'Single-agent analyst that mirrors the Agno-based startup trend project with DuckDuckGo research and report-ready output.',
    category: 'Data & Analytics',
    icon: <BarChart className="w-5 h-5" />,
    rating: 4.8,
    downloads: 655,
    featured: true,
    tags: ['agno', 'analytics', 'duckduckgo'],
    config: {
      head: createNode('head-trend', 'gpt4o-mini', 'Market Pulse Analyst', 'head', '#10a37f', 'Head', {
        model: 'gpt-4o-mini',
        temperature: 0.5,
        systemPrompt: 'Track startup traction signals and produce concise investment notes.',
      }),
      arms: [
        createNode('arm-trend-1', 'tavily-search', 'DuckDuckGo Research Proxy', 'arm', '#3b82f6', 'Tool', {
          searchDepth: 'advanced',
          include_answer: true,
          maxResults: 6,
        }),
        createNode('arm-trend-2', 'http-tool', 'News Snapshot Fetcher', 'arm', '#3b82f6', 'Tool', {
          baseUrl: 'https://newsapi.org',
          timeout: 45,
        }),
      ],
      heart: createNode('heart-trend', 'convo-memory', 'Trend Notebook', 'heart', '#ec4899', 'Memory', {
        maxMessages: 10,
        summaryThreshold: 8,
      }),
      leg: createNode('leg-trend', 'single-agent', 'Agno Insight Loop', 'leg', '#f97316', 'Execution', {
        mode: 'single',
        autonomous: true,
      }),
      spine: createNode('spine-trend', 'allowed-domains', 'Trusted News Guard', 'spine', '#06b6d4', 'Guardrail', {
        domains: ['news.ycombinator.com', 'techcrunch.com'],
        blockByDefault: true,
      }),
    },
  },
  {
    id: 'blueprint-agno-rag',
    name: 'Deepseek RAG Lab',
    description: 'Local retrieval lab inspired by the Deepseek + Qdrant Agno project, tuned for Ollama-hosted models and Exa ingestion.',
    category: 'Data & Analytics',
    icon: <FileSearch className="w-5 h-5" />,
    rating: 4.7,
    downloads: 512,
    featured: false,
    tags: ['agno', 'rag', 'ollama'],
    config: {
      head: createNode('head-rag', 'gpt4o-mini', 'Knowledge Router', 'head', '#10a37f', 'Head', {
        temperature: 0.4,
        systemPrompt: 'Coordinate Deepseek retrieval chains with local Qdrant context.',
      }),
      arms: [
        createNode('arm-rag-1', 'http-tool', 'Qdrant Vector API', 'arm', '#3b82f6', 'Tool', {
          baseUrl: 'http://localhost:6333',
          description: 'Query local Qdrant collections for context passages.',
        }),
        createNode('arm-rag-2', 'tavily-search', 'Exa Web Sweep', 'arm', '#3b82f6', 'Tool', {
          searchDepth: 'advanced',
          maxResults: 4,
        }),
      ],
      heart: createNode('heart-rag', 'convo-memory', 'Vector Memory Plan', 'heart', '#ec4899', 'Memory', {
        maxMessages: 8,
        summaryThreshold: 6,
      }),
      leg: createNode('leg-rag', 'single-agent', 'Local RAG Loop', 'leg', '#f97316', 'Execution', {
        mode: 'single',
        autonomous: true,
      }),
      spine: createNode('spine-rag', 'max-tool-calls', 'Latency Guard', 'spine', '#06b6d4', 'Guardrail', {
        maxCalls: 5,
        timeWindow: '1m',
      }),
    },
  },
  {
    id: 'blueprint-agno-travel',
    name: 'Travel Planner MCP Team',
    description: 'MCP-backed itinerary squad that mirrors the Agno travel planner setup with Google APIs and Streamlit control.',
    category: 'Productivity',
    icon: <Calendar className="w-5 h-5" />,
    rating: 4.8,
    downloads: 704,
    featured: true,
    tags: ['agno', 'mcp', 'travel'],
    config: {
      head: createNode('head-travel', 'gpt4o-mini', 'Trip Coordinator', 'head', '#10a37f', 'Head', {
        temperature: 0.55,
        systemPrompt: 'Own the traveler brief, coordinate MCP itinerary tasks, and confirm availability.',
      }),
      arms: [
        createNode('arm-travel-1', 'mcp-tool', 'MCP Travel Desk', 'arm', '#3b82f6', 'Tool', {
          serverLabel: 'Travel Planner MCP',
          transportType: 'streamable-http',
          allowedTools: ['search-itinerary', 'fetch-flight-data'],
        }),
        createNode('arm-travel-2', 'http-tool', 'Google Calendar Bridge', 'arm', '#3b82f6', 'Tool', {
          baseUrl: 'https://www.googleapis.com/calendar/v3',
          defaultHeaders: {
            Authorization: 'Bearer ${GOOGLE_OAUTH_TOKEN}',
          },
        }),
      ],
      heart: createNode('heart-travel', 'convo-memory', 'Traveler Preferences', 'heart', '#ec4899', 'Memory', {
        maxMessages: 14,
        summaryThreshold: 10,
      }),
      leg: createNode('leg-travel', 'team', 'MCP Team Workflow', 'leg', '#a855f7', 'Execution', {
        mode: 'team',
        coordinator: 'plan-then-book',
      }),
      spine: createNode('spine-travel', 'allowed-domains', 'Itinerary Guard', 'spine', '#06b6d4', 'Guardrail', {
        domains: ['googleapis.com', 'maps.googleapis.com'],
        blockByDefault: true,
      }),
      teamMembers: [
        {
          id: 'travel-navigator',
          name: 'Itinerary Architect',
          role: 'Draft multi-city route options',
          head: createNode('head-travel-navigator', 'gpt4o-mini', 'Navigator Head', 'head', '#10a37f', 'Head', {
            temperature: 0.6,
            systemPrompt: 'Use MCP tools to stitch flights, rail, and hotel options.',
          }),
          arms: [
            createNode('arm-travel-navigator', 'mcp-tool', 'Airport Finder', 'arm', '#3b82f6', 'Tool', {
              serverLabel: 'Travel Planner MCP',
            }),
          ],
        },
        {
          id: 'travel-liaison',
          name: 'Calendar Liaison',
          role: 'Sync bookings to shared calendars',
          head: createNode('head-travel-liaison', 'gpt4o-mini', 'Liaison Head', 'head', '#10a37f', 'Head', {
            temperature: 0.4,
            systemPrompt: 'Validate time zones and document confirmations.',
          }),
          arms: [
            createNode('arm-travel-liaison', 'http-tool', 'Calendar Sync', 'arm', '#3b82f6', 'Tool', {
              baseUrl: 'https://www.googleapis.com/calendar/v3',
            }),
          ],
          heart: createNode('heart-travel-liaison', 'convo-memory', 'Guest Preferences', 'heart', '#ec4899', 'Memory', {
            maxMessages: 6,
          }),
        },
      ],
    },
  },
  {
    id: 'blueprint-agno-legal',
    name: 'Legal Research Collective',
    description: 'Team-mode legal brief generator that follows the Agno legal agent setup with Qdrant memory and Ollama case review.',
    category: 'Productivity',
    icon: <Shield className="w-5 h-5" />,
    rating: 4.7,
    downloads: 498,
    featured: false,
    tags: ['agno', 'qdrant', 'briefs'],
    config: {
      head: createNode('head-legal', 'gpt4o-mini', 'Lead Counsel', 'head', '#10a37f', 'Head', {
        temperature: 0.45,
        systemPrompt: 'Coordinate statute research, retrieval, and final brief drafting.',
      }),
      arms: [
        createNode('arm-legal-1', 'tavily-search', 'Case Law Search', 'arm', '#3b82f6', 'Tool', {
          searchDepth: 'advanced',
          include_answer: true,
        }),
        createNode('arm-legal-2', 'http-tool', 'Qdrant Brief Bank', 'arm', '#3b82f6', 'Tool', {
          baseUrl: 'http://localhost:6333',
        }),
      ],
      heart: createNode('heart-legal', 'convo-memory', 'Matter Notebook', 'heart', '#ec4899', 'Memory', {
        maxMessages: 12,
        summaryThreshold: 9,
      }),
      leg: createNode('leg-legal', 'team', 'Agno Legal Workflow', 'leg', '#a855f7', 'Execution', {
        mode: 'team',
      }),
      spine: createNode('spine-legal', 'max-tool-calls', 'Confidentiality Guard', 'spine', '#06b6d4', 'Guardrail', {
        maxCalls: 6,
        timeWindow: '90s',
      }),
      teamMembers: [
        {
          id: 'legal-researcher',
          name: 'Research Specialist',
          role: 'Surface statutes and precedent',
          head: createNode('head-legal-researcher', 'gpt4o-mini', 'Research Head', 'head', '#10a37f', 'Head', {
            temperature: 0.35,
            systemPrompt: 'Prioritize primary sources and summarize holdings.',
          }),
          arms: [
            createNode('arm-legal-researcher', 'tavily-search', 'Legal Search', 'arm', '#3b82f6', 'Tool', {
              searchDepth: 'advanced',
            }),
          ],
        },
        {
          id: 'legal-drafter',
          name: 'Brief Drafter',
          role: 'Assemble memos and action steps',
          head: createNode('head-legal-drafter', 'gpt4o-mini', 'Drafter Head', 'head', '#10a37f', 'Head', {
            temperature: 0.55,
            systemPrompt: 'Produce structured memos referencing retrieved records.',
          }),
          arms: [
            createNode('arm-legal-drafter', 'http-tool', 'Qdrant Knowledge Pull', 'arm', '#3b82f6', 'Tool', {
              baseUrl: 'http://localhost:6333',
            }),
          ],
          heart: createNode('heart-legal-drafter', 'convo-memory', 'Citation Scratchpad', 'heart', '#ec4899', 'Memory', {
            maxMessages: 5,
          }),
        },
      ],
    },
  },
  {
    id: 'blueprint-agno-voice-support',
    name: 'Voice Support Concierge',
    description: 'Customer-support voice agent inspired by the Streamlit voice concierge in awesome-llm-apps; handles tickets, knowledge lookups, and Twilio-style call actions.',
    category: 'Customer Support',
    icon: <MessageSquare className="w-5 h-5" />,
    rating: 4.6,
    downloads: 583,
    featured: false,
    tags: ['agno', 'voice', 'support'],
    config: {
      head: createNode('head-voice', 'gpt4o-mini', 'Voice Console', 'head', '#10a37f', 'Head', {
        temperature: 0.65,
        systemPrompt: 'Resolve support calls, summarize outcomes, and trigger follow-up tickets when needed.',
      }),
      arms: [
        createNode('arm-voice-1', 'http-tool', 'Telephony Bridge', 'arm', '#3b82f6', 'Tool', {
          baseUrl: 'https://api.twilio.com',
          defaultHeaders: { Authorization: 'Basic ${TWILIO_AUTH}' },
          timeout: 30,
        }),
        createNode('arm-voice-2', 'tavily-search', 'Knowledge Lookup', 'arm', '#3b82f6', 'Tool', {
          searchDepth: 'basic',
          include_answer: true,
          maxResults: 4,
        }),
      ],
      heart: createNode('heart-voice', 'convo-memory', 'Call Log Memory', 'heart', '#ec4899', 'Memory', {
        maxMessages: 15,
        summaryThreshold: 10,
      }),
      leg: createNode('leg-voice', 'single-agent', 'Voice Loop', 'leg', '#f97316', 'Execution', {
        mode: 'single',
        autonomous: true,
      }),
      spine: createNode('spine-voice', 'allowed-domains', 'Compliance Guard', 'spine', '#06b6d4', 'Guardrail', {
        domains: ['twilio.com', 'zendesk.com'],
        blockByDefault: true,
      }),
    },
  },
  {
    id: 'blueprint-agno-research-writer',
    name: 'Research & Writing Team',
    description: 'Two-agent Agno team from the awesome-llm-apps research/writing workflow: one agent gathers facts, another drafts polished copy.',
    category: 'Content Creation',
    icon: <FileSearch className="w-5 h-5" />,
    rating: 4.9,
    downloads: 941,
    featured: true,
    tags: ['agno', 'team', 'content'],
    config: {
      head: createNode('head-rw', 'gpt4o-mini', 'Team Coordinator', 'head', '#10a37f', 'Head', {
        temperature: 0.6,
        systemPrompt: 'Delegate research to specialists and deliver structured long-form content with sources.',
      }),
      arms: [
        createNode('arm-rw-1', 'tavily-search', 'Research Search', 'arm', '#3b82f6', 'Tool', {
          searchDepth: 'advanced',
          include_answer: true,
          maxResults: 6,
        }),
      ],
      leg: createNode('leg-rw', 'team', 'Research Team Mode', 'leg', '#a855f7', 'Execution', {
        mode: 'team',
      }),
      heart: createNode('heart-rw', 'convo-memory', 'Editorial Memory', 'heart', '#ec4899', 'Memory', {
        maxMessages: 10,
        summaryThreshold: 8,
      }),
      teamMembers: [
        {
          id: 'rw-researcher',
          name: 'Research Specialist',
          role: 'Collect and summarize references',
          head: createNode('head-rw-research', 'gpt4o-mini', 'Research Head', 'head', '#10a37f', 'Head', {
            temperature: 0.4,
            systemPrompt: 'Focus on facts, citations, and quote extraction for the writing agent.',
          }),
          arms: [
            createNode('arm-rw-research', 'tavily-search', 'Fact Finder', 'arm', '#3b82f6', 'Tool', {
              searchDepth: 'advanced',
              include_answer: false,
            }),
          ],
        },
        {
          id: 'rw-writer',
          name: 'Content Writer',
          role: 'Produce narrative output',
          head: createNode('head-rw-writer', 'gpt4o-mini', 'Writer Head', 'head', '#10a37f', 'Head', {
            temperature: 0.75,
            systemPrompt: 'Craft engaging drafts, ensuring structure and tone guidance are applied.',
          }),
          arms: [],
          heart: createNode('heart-rw-writer', 'convo-memory', 'Style Notes', 'heart', '#ec4899', 'Memory', {
            maxMessages: 6,
          }),
        },
      ],
    },
  },
  {
    id: 'blueprint-agno-github',
    name: 'GitHub API Assistant',
    description: 'Productivity agent modeled after the awesome-llm-apps GitHub API helper that triages repos, PRs, and issues via Agno tools.',
    category: 'Productivity',
    icon: <Code className="w-5 h-5" />,
    rating: 4.5,
    downloads: 621,
    featured: false,
    tags: ['agno', 'github', 'automation'],
    config: {
      head: createNode('head-gh', 'gpt4o-mini', 'Repo Operator', 'head', '#10a37f', 'Head', {
        temperature: 0.45,
        systemPrompt: 'Manage GitHub repos, summarize PRs, and suggest actions following the REST guide.',
      }),
      arms: [
        createNode('arm-gh-1', 'http-tool', 'GitHub REST Client', 'arm', '#3b82f6', 'Tool', {
          baseUrl: 'https://api.github.com',
          defaultHeaders: {
            Authorization: 'Bearer ${GITHUB_TOKEN}',
            Accept: 'application/vnd.github+json',
          },
          timeout: 60,
        }),
        createNode('arm-gh-2', 'tavily-search', 'Docs Lookup', 'arm', '#3b82f6', 'Tool', {
          searchDepth: 'basic',
          include_answer: false,
          maxResults: 3,
        }),
      ],
      leg: createNode('leg-gh', 'single-agent', 'Automation Loop', 'leg', '#f97316', 'Execution', {
        mode: 'single',
      }),
      spine: createNode('spine-gh', 'max-tool-calls', 'API Rate Guard', 'spine', '#06b6d4', 'Guardrail', {
        maxCalls: 10,
        timeWindow: '1m',
      }),
    },
  },
  {
    id: 'blueprint-agno-crypto',
    name: 'Crypto Market Monitor',
    description: 'CoinGecko-powered blueprint aligned with the awesome-llm-apps crypto tracker; produces dashboards and alerts inside Agno.',
    category: 'Data & Analytics',
    icon: <DollarSign className="w-5 h-5" />,
    rating: 4.6,
    downloads: 577,
    featured: false,
    tags: ['agno', 'crypto', 'markets'],
    config: {
      head: createNode('head-crypto', 'gpt4o-mini', 'Market Strategist', 'head', '#10a37f', 'Head', {
        temperature: 0.4,
        systemPrompt: 'Summarize price action, risk, and catalysts for tracked tokens.',
      }),
      arms: [
        createNode('arm-crypto-1', 'http-tool', 'CoinGecko API', 'arm', '#3b82f6', 'Tool', {
          baseUrl: 'https://api.coingecko.com/api/v3',
          timeout: 45,
        }),
        createNode('arm-crypto-2', 'http-tool', 'News Sentiment Fetcher', 'arm', '#3b82f6', 'Tool', {
          baseUrl: 'https://cryptopanic.com/api',
        }),
      ],
      heart: createNode('heart-crypto', 'convo-memory', 'Token Watchlist', 'heart', '#ec4899', 'Memory', {
        maxMessages: 9,
        summaryThreshold: 7,
      }),
      leg: createNode('leg-crypto', 'single-agent', 'Market Loop', 'leg', '#f97316', 'Execution', {
        mode: 'single',
        autonomous: true,
      }),
      spine: createNode('spine-crypto', 'max-tool-calls', 'Rate Guard', 'spine', '#06b6d4', 'Guardrail', {
        maxCalls: 6,
        timeWindow: '1m',
      }),
    },
  },
  {
    id: 'blueprint-agno-news',
    name: 'News Pulse Aggregator',
    description: 'Streaming news monitor modeled after the awesome-llm-apps Tavily News Aggregator blueprint, combining rapid search sweeps with recap reports.',
    category: 'Data & Analytics',
    icon: <Sparkles className="w-5 h-5" />,
    rating: 4.7,
    downloads: 688,
    featured: false,
    tags: ['news', 'tavily', 'reports'],
    config: {
      head: createNode('head-news', 'gpt4o-mini', 'News Director', 'head', '#10a37f', 'Head', {
        temperature: 0.5,
        systemPrompt: 'Track headlines from the last 48 hours and summarize perspectives.',
      }),
      arms: [
        createNode('arm-news-1', 'tavily-search', 'Breaking Search', 'arm', '#3b82f6', 'Tool', {
          searchDepth: 'advanced',
          include_answer: true,
          maxResults: 6,
        }),
        createNode('arm-news-2', 'http-tool', 'NewsAPI Fetcher', 'arm', '#3b82f6', 'Tool', {
          baseUrl: 'https://newsapi.org/v2',
          timeout: 40,
        }),
      ],
      leg: createNode('leg-news', 'single-agent', 'Daily Pulse Loop', 'leg', '#f97316', 'Execution', {
        mode: 'single',
      }),
    },
  },
  {
    id: 'blueprint-agno-powerhouse',
    name: 'Research Powerhouse',
    description: 'Dual-tool investigative assistant from awesome-llm-apps that marries Tavily context with REST API enrichment.',
    category: 'Productivity',
    icon: <FileSearch className="w-5 h-5" />,
    rating: 4.8,
    downloads: 712,
    featured: true,
    tags: ['research', 'rest', 'tavily'],
    config: {
      head: createNode('head-power', 'gpt4o-mini', 'Investigator', 'head', '#10a37f', 'Head', {
        temperature: 0.55,
        systemPrompt: 'Cross-check facts between search snippets and API payloads to build comprehensive briefs.',
      }),
      arms: [
        createNode('arm-power-1', 'tavily-search', 'Context Sweep', 'arm', '#3b82f6', 'Tool', {
          searchDepth: 'advanced',
          include_answer: true,
        }),
        createNode('arm-power-2', 'http-tool', 'REST Data Tap', 'arm', '#3b82f6', 'Tool', {
          baseUrl: '',
          description: 'Call any REST API specified by the user to enrich findings.',
        }),
      ],
      heart: createNode('heart-power', 'convo-memory', 'Research Notes', 'heart', '#ec4899', 'Memory', {
        maxMessages: 9,
      }),
      leg: createNode('leg-power', 'single-agent', 'Synthesis Loop', 'leg', '#f97316', 'Execution', {
        mode: 'single',
      }),
    },
  },
  {
    id: 'blueprint-agno-awsdocs',
    name: 'AWS Docs Navigator',
    description: 'MCP-powered assistant matching the AWS Documentation Expert blueprint to query and summarize AWS guides.',
    category: 'Productivity',
    icon: <Shield className="w-5 h-5" />,
    rating: 4.6,
    downloads: 431,
    featured: false,
    tags: ['aws', 'docs', 'mcp'],
    config: {
      head: createNode('head-aws', 'gpt4o-mini', 'Cloud Guide', 'head', '#10a37f', 'Head', {
        temperature: 0.4,
        systemPrompt: 'Answer AWS architecture questions with citations to official docs.',
      }),
      arms: [
        createNode('arm-aws-1', 'mcp-tool', 'AWS Docs MCP', 'arm', '#3b82f6', 'Tool', {
          serverLabel: 'aws-docs',
          transportType: 'streamable-http',
          allowedTools: ['search', 'get-page'],
        }),
      ],
      leg: createNode('leg-aws', 'single-agent', 'Doc Lookup Loop', 'leg', '#f97316', 'Execution', {
        mode: 'single',
      }),
      spine: createNode('spine-aws', 'allowed-domains', 'Docs Guard', 'spine', '#06b6d4', 'Guardrail', {
        domains: ['aws.amazon.com'],
        blockByDefault: true,
      }),
    },
  },
  {
    id: 'blueprint-agno-rest',
    name: 'REST API Tester',
    description: 'Developer-focused utility blueprint from awesome-llm-apps that crafts requests, inspects responses, and debugs APIs.',
    category: 'Productivity',
    icon: <Code className="w-5 h-5" />,
    rating: 4.5,
    downloads: 509,
    featured: false,
    tags: ['api', 'debug', 'automation'],
    config: {
      head: createNode('head-rest', 'gpt4o-mini', 'API Inspector', 'head', '#10a37f', 'Head', {
        temperature: 0.3,
        systemPrompt: 'Craft HTTP requests, validate responses, and suggest fixes.',
      }),
      arms: [
        createNode('arm-rest-1', 'http-tool', 'REST Client', 'arm', '#3b82f6', 'Tool', {
          baseUrl: '',
          description: 'Supports GET/POST/PUT/PATCH/DELETE with custom headers and bodies.',
        }),
      ],
      leg: createNode('leg-rest', 'single-agent', 'Testing Loop', 'leg', '#f97316', 'Execution', {
        mode: 'single',
      }),
      spine: createNode('spine-rest', 'timeout', 'Timeout Guard', 'spine', '#06b6d4', 'Guardrail', {
        duration: 45,
      }),
    },
  },
  {
    id: 'blueprint-agno-weather',
    name: 'Weather Forecaster',
    description: 'OpenWeatherMap assistant from the marketplace set that surfaces forecasts, alerts, and travel-ready tips.',
    category: 'Productivity',
    icon: <Calendar className="w-5 h-5" />,
    rating: 4.4,
    downloads: 562,
    featured: false,
    tags: ['weather', 'travel', 'api'],
    config: {
      head: createNode('head-weather', 'gpt4o-mini', 'Forecast Brain', 'head', '#10a37f', 'Head', {
        temperature: 0.45,
        systemPrompt: 'Explain weather trends, units, and planning guidance.',
      }),
      arms: [
        createNode('arm-weather-1', 'http-tool', 'OpenWeatherMap', 'arm', '#3b82f6', 'Tool', {
          baseUrl: 'https://api.openweathermap.org/data/2.5',
          timeout: 30,
        }),
      ],
      leg: createNode('leg-weather', 'single-agent', 'Forecast Loop', 'leg', '#f97316', 'Execution', {
        mode: 'single',
      }),
    },
  },
  {
    id: 'blueprint-agno-scraper',
    name: 'Web Scraping Scout',
    description: 'Browserless-style scraping helper inspired by the awesome-llm-apps web scraping agent, tuned for lead capture.',
    category: 'Sales & Marketing',
    icon: <Sparkles className="w-5 h-5" />,
    rating: 4.5,
    downloads: 467,
    featured: false,
    tags: ['scraping', 'leads', 'automation'],
    config: {
      head: createNode('head-scraper', 'gpt4o-mini', 'Scraping Planner', 'head', '#10a37f', 'Head', {
        temperature: 0.5,
        systemPrompt: 'Plan scraping runs, summarize extracted data, and respect robots instructions.',
      }),
      arms: [
        createNode('arm-scraper-1', 'http-tool', 'Browserless API', 'arm', '#3b82f6', 'Tool', {
          baseUrl: 'https://api.browserless.io',
          timeout: 60,
        }),
      ],
      leg: createNode('leg-scraper', 'single-agent', 'Scrape Loop', 'leg', '#f97316', 'Execution', {
        mode: 'single',
      }),
      spine: createNode('spine-scraper', 'allowed-domains', 'Compliance Filter', 'spine', '#06b6d4', 'Guardrail', {
        blockByDefault: false,
      }),
    },
  },
  {
    id: 'blueprint-agno-viz',
    name: 'Data Viz Analyst',
    description: 'Visualization-first assistant from the AI data visualisation agent tutorial, generating charts and dashboards.',
    category: 'Data & Analytics',
    icon: <BarChart className="w-5 h-5" />,
    rating: 4.7,
    downloads: 544,
    featured: false,
    tags: ['viz', 'reports', 'dashboards'],
    config: {
      head: createNode('head-viz', 'gpt4o-mini', 'Viz Strategist', 'head', '#10a37f', 'Head', {
        temperature: 0.5,
        systemPrompt: 'Summarize datasets and recommend chart types before rendering specs.',
      }),
      arms: [
        createNode('arm-viz-1', 'http-tool', 'Plot API', 'arm', '#3b82f6', 'Tool', {
          baseUrl: 'https://api.plotapi.com',
        }),
        createNode('arm-viz-2', 'tavily-search', 'Benchmark Lookup', 'arm', '#3b82f6', 'Tool', {
          searchDepth: 'basic',
        }),
      ],
      heart: createNode('heart-viz', 'convo-memory', 'Insight Memory', 'heart', '#ec4899', 'Memory', {
        maxMessages: 8,
      }),
      leg: createNode('leg-viz', 'single-agent', 'Visualization Loop', 'leg', '#f97316', 'Execution', {
        mode: 'single',
      }),
    },
  },
  {
    id: 'blueprint-agno-travel-lite',
    name: 'Travel Companion Lite',
    description: 'Single-agent variant of the AI travel planner that balances itinerary generation with budget heuristics.',
    category: 'Productivity',
    icon: <Calendar className="w-5 h-5" />,
    rating: 4.6,
    downloads: 598,
    featured: false,
    tags: ['travel', 'planning', 'itinerary'],
    config: {
      head: createNode('head-travel-lite', 'gpt4o-mini', 'Trip Designer', 'head', '#10a37f', 'Head', {
        temperature: 0.65,
        systemPrompt: 'Create balanced itineraries with lodging, dining, and logistics tips.',
      }),
      arms: [
        createNode('arm-travel-lite-1', 'tavily-search', 'Destination Research', 'arm', '#3b82f6', 'Tool', {
          searchDepth: 'advanced',
        }),
        createNode('arm-travel-lite-2', 'http-tool', 'Flight Finder', 'arm', '#3b82f6', 'Tool', {
          baseUrl: 'https://api.duffel.com',
        }),
      ],
      leg: createNode('leg-travel-lite', 'single-agent', 'Planning Loop', 'leg', '#f97316', 'Execution', {
        mode: 'single',
      }),
      heart: createNode('heart-travel-lite', 'convo-memory', 'Preference Memory', 'heart', '#ec4899', 'Memory', {
        maxMessages: 9,
      }),
    },
  },
  {
    id: 'blueprint-agno-medical',
    name: 'Medical Imaging Analyst',
    description: 'Healthcare-focused workflow based on the AI medical imaging agent tutorial, summarizing scan findings with guardrails.',
    category: 'Data & Analytics',
    icon: <Shield className="w-5 h-5" />,
    rating: 4.5,
    downloads: 458,
    featured: false,
    tags: ['medical', 'imaging', 'analysis'],
    config: {
      head: createNode('head-medical', 'gpt4o-mini', 'Radiology Assistant', 'head', '#10a37f', 'Head', {
        temperature: 0.35,
        systemPrompt: 'Provide educational imaging summaries and highlight follow-up questions; do not give diagnoses.',
      }),
      arms: [
        createNode('arm-medical-1', 'http-tool', 'Scan Review API', 'arm', '#3b82f6', 'Tool', {
          baseUrl: 'https://medical-files.api',
          description: 'Fetches imaging notes and metadata for review',
        }),
        createNode('arm-medical-2', 'tavily-search', 'Guideline Lookup', 'arm', '#3b82f6', 'Tool', {
          searchDepth: 'basic',
        }),
      ],
      leg: createNode('leg-medical', 'single-agent', 'Analysis Loop', 'leg', '#f97316', 'Execution', {
        mode: 'single',
      }),
      spine: createNode('spine-medical', 'allowed-domains', 'Safety Guard', 'spine', '#06b6d4', 'Guardrail', {
        blockByDefault: true,
        domains: ['nih.gov', 'who.int', 'nejm.org'],
      }),
    },
  },
  {
    id: 'blueprint-agno-data-analysis',
    name: 'Data Analysis Coach',
    description: 'Starter AI data analysis agent blueprint from awesome-llm-apps, focusing on CSV/SQL insights and storytelling.',
    category: 'Data & Analytics',
    icon: <BarChart className="w-5 h-5" />,
    rating: 4.8,
    downloads: 803,
    featured: true,
    tags: ['analysis', 'sql', 'reports'],
    config: {
      head: createNode('head-analysis', 'gpt4o-mini', 'Insight Coach', 'head', '#10a37f', 'Head', {
        temperature: 0.45,
        systemPrompt: 'Explore datasets, run lightweight SQL, and narrate findings.',
      }),
      arms: [
        createNode('arm-analysis-1', 'http-tool', 'Analytics API', 'arm', '#3b82f6', 'Tool', {
          baseUrl: 'https://analytics.api',
          description: 'Runs SQL workloads via REST endpoint',
        }),
        createNode('arm-analysis-2', 'http-tool', 'Data Lake Connector', 'arm', '#3b82f6', 'Tool', {
          baseUrl: 'https://storage.api',
          description: 'Loads CSV/XLSX content for analysis',
        }),
      ],
      heart: createNode('heart-analysis', 'convo-memory', 'Findings Memory', 'heart', '#ec4899', 'Memory', {
        maxMessages: 11,
      }),
      leg: createNode('leg-analysis', 'single-agent', 'Analysis Loop', 'leg', '#f97316', 'Execution', {
        mode: 'single',
      }),
    },
  },
  {
    id: 'blueprint-agno-blog-podcast',
    name: 'Blog-to-Podcast Studio',
    description: 'Content pipeline from the Blog-to-Podcast agent that ingests articles, drafts scripts, and outputs narration-ready text.',
    category: 'Content Creation',
    icon: <Sparkles className="w-5 h-5" />,
    rating: 4.7,
    downloads: 734,
    featured: false,
    tags: ['podcast', 'content', 'audio'],
    config: {
      head: createNode('head-blogcast', 'gpt4o-mini', 'Narrative Director', 'head', '#10a37f', 'Head', {
        temperature: 0.65,
        systemPrompt: 'Transform long-form posts into engaging podcast scripts with hooks and CTAs.',
      }),
      arms: [
        createNode('arm-blogcast-1', 'http-tool', 'Content Fetcher', 'arm', '#3b82f6', 'Tool', {
          baseUrl: 'https://content.api',
          description: 'Retrieves blog posts or RSS entries',
        }),
        createNode('arm-blogcast-2', 'http-tool', 'TTS Bridge', 'arm', '#3b82f6', 'Tool', {
          baseUrl: 'https://api.openai.com/v1/audio',
        }),
      ],
      heart: createNode('heart-blogcast', 'convo-memory', 'Tone Memory', 'heart', '#ec4899', 'Memory', {
        maxMessages: 8,
      }),
      leg: createNode('leg-blogcast', 'single-agent', 'Studio Loop', 'leg', '#f97316', 'Execution', {
        mode: 'single',
      }),
    },
  },
  {
    id: 'blueprint-agno-meme',
    name: 'AI Meme Generator',
    description: 'Browser-use meme lab from awesome-llm-apps that drafts captions and triggers image edits.',
    category: 'Content Creation',
    icon: <Sparkles className="w-5 h-5" />,
    rating: 4.5,
    downloads: 689,
    featured: false,
    tags: ['meme', 'social', 'browser'],
    config: {
      head: createNode('head-meme', 'gpt4o-mini', 'Meme Director', 'head', '#10a37f', 'Head', {
        temperature: 0.8,
        systemPrompt: 'Produce witty meme text and describe visual layouts.',
      }),
      arms: [
        createNode('arm-meme-1', 'http-tool', 'BrowserUse Controller', 'arm', '#3b82f6', 'Tool', {
          baseUrl: 'https://api.browseruse.com',
        }),
      ],
      leg: createNode('leg-meme', 'single-agent', 'Creative Loop', 'leg', '#f97316', 'Execution', {
        mode: 'single',
      }),
    },
  },
  {
    id: 'blueprint-agno-investment',
    name: 'Investment Insight Desk',
    description: 'Streamlit AI investment agent blueprint redesigned for Agno with market data tools and guardrails.',
    category: 'Sales & Marketing',
    icon: <DollarSign className="w-5 h-5" />,
    rating: 4.6,
    downloads: 612,
    featured: false,
    tags: ['finance', 'investment', 'advisor'],
    config: {
      head: createNode('head-investment', 'gpt4o-mini', 'Portfolio Strategist', 'head', '#10a37f', 'Head', {
        temperature: 0.45,
        systemPrompt: 'Summarize opportunities and risks. Provide educational insights, not financial advice.',
      }),
      arms: [
        createNode('arm-investment-1', 'http-tool', 'Market Data API', 'arm', '#3b82f6', 'Tool', {
          baseUrl: 'https://api.polygon.io',
        }),
        createNode('arm-investment-2', 'tavily-search', 'News Sweep', 'arm', '#3b82f6', 'Tool', {
          searchDepth: 'basic',
        }),
      ],
      heart: createNode('heart-investment', 'convo-memory', 'Investor Preferences', 'heart', '#ec4899', 'Memory', {
        maxMessages: 7,
      }),
      leg: createNode('leg-investment', 'single-agent', 'Briefing Loop', 'leg', '#f97316', 'Execution', {
        mode: 'single',
      }),
      spine: createNode('spine-investment', 'allowed-domains', 'Compliance Note', 'spine', '#06b6d4', 'Guardrail', {
        blockByDefault: true,
        domains: ['sec.gov', 'investor.gov'],
      }),
    },
  },
  {
    id: 'blueprint-agno-teaching-team',
    name: 'Teaching Agent Team',
    description: 'Multi-agent classroom assistant described in the awesome-llm-apps teaching team tutorial, producing roadmaps and exercises.',
    category: 'Productivity',
    icon: <Calendar className="w-5 h-5" />,
    rating: 4.9,
    downloads: 780,
    featured: true,
    tags: ['education', 'team', 'google-docs'],
    config: {
      head: createNode('head-teach', 'gpt4o-mini', 'Lead Instructor', 'head', '#10a37f', 'Head', {
        temperature: 0.6,
        systemPrompt: 'Coordinate academic planning, exercises, and resource lists in Google Docs style.',
      }),
      arms: [
        createNode('arm-teach-1', 'http-tool', 'Docs API', 'arm', '#3b82f6', 'Tool', {
          baseUrl: 'https://docs.googleapis.com/v1',
        }),
      ],
      leg: createNode('leg-teach', 'team', 'Team Execution', 'leg', '#a855f7', 'Execution', {
        mode: 'team',
      }),
      teamMembers: [
        {
          id: 'teach-advisor',
          name: 'Academic Advisor',
          role: 'Designs learning paths',
          head: createNode('head-teach-advisor', 'gpt4o-mini', 'Advisor Head', 'head', '#10a37f', 'Head', {
            temperature: 0.5,
            systemPrompt: 'Lay out milestones with prerequisites and time estimates.',
          }),
          arms: [],
        },
        {
          id: 'teach-assistant',
          name: 'Teaching Assistant',
          role: 'Builds exercises',
          head: createNode('head-teach-assistant', 'gpt4o-mini', 'Assistant Head', 'head', '#10a37f', 'Head', {
            temperature: 0.55,
            systemPrompt: 'Create practice problems with solutions and difficulty tags.',
          }),
          arms: [],
        },
      ],
    },
  },
  {
    id: 'blueprint-agno-aqi',
    name: 'AQI Analysis Lab',
    description: 'Air quality analyst blueprint referencing the AQI agent tutorial, blending Tavily context with AQI API queries.',
    category: 'Data & Analytics',
    icon: <Shield className="w-5 h-5" />,
    rating: 4.6,
    downloads: 533,
    featured: false,
    tags: ['aqi', 'environment', 'reports'],
    config: {
      head: createNode('head-aqi', 'gpt4o-mini', 'AQI Scientist', 'head', '#10a37f', 'Head', {
        temperature: 0.45,
        systemPrompt: 'Explain AQI readings and mitigation steps clearly.',
      }),
      arms: [
        createNode('arm-aqi-1', 'http-tool', 'OpenAQ', 'arm', '#3b82f6', 'Tool', {
          baseUrl: 'https://api.openaq.org/v2',
        }),
        createNode('arm-aqi-2', 'tavily-search', 'Local News Scan', 'arm', '#3b82f6', 'Tool', {
          searchDepth: 'basic',
        }),
      ],
      leg: createNode('leg-aqi', 'single-agent', 'AQI Loop', 'leg', '#f97316', 'Execution', {
        mode: 'single',
      }),
      spine: createNode('spine-aqi', 'max-tool-calls', 'Rate Guard', 'spine', '#06b6d4', 'Guardrail', {
        maxCalls: 6,
      }),
    },
  },
  {
    id: 'blueprint-agno-deep-research',
    name: 'Deep Research Agent',
    description: 'Single-agent deep research workflow with Composio integrations per the advanced tutorial.',
    category: 'Productivity',
    icon: <FileSearch className="w-5 h-5" />,
    rating: 4.7,
    downloads: 701,
    featured: false,
    tags: ['research', 'composio', 'docs'],
    config: {
      head: createNode('head-deep', 'gpt4o-mini', 'Research Strategist', 'head', '#10a37f', 'Head', {
        temperature: 0.5,
        systemPrompt: 'Run deep-dive investigations, pulling Google Docs and Perplexity snippets.',
      }),
      arms: [
        createNode('arm-deep-1', 'http-tool', 'Perplexity API', 'arm', '#3b82f6', 'Tool', {
          baseUrl: 'https://api.perplexity.ai',
        }),
        createNode('arm-deep-2', 'http-tool', 'Google Docs Fetcher', 'arm', '#3b82f6', 'Tool', {
          baseUrl: 'https://docs.googleapis.com/v1',
        }),
      ],
      heart: createNode('heart-deep', 'convo-memory', 'Finding Memory', 'heart', '#ec4899', 'Memory', {
        maxMessages: 9,
      }),
      leg: createNode('leg-deep', 'single-agent', 'Investigation Loop', 'leg', '#f97316', 'Execution', {
        mode: 'single',
      }),
    },
  },
  {
    id: 'blueprint-agno-game-design',
    name: 'Game Design Team',
    description: 'Creative game design squad from the AI game design agent team tutorial, delivering pitch docs and mechanics.',
    category: 'Content Creation',
    icon: <Sparkles className="w-5 h-5" />,
    rating: 4.8,
    downloads: 564,
    featured: false,
    tags: ['game', 'team', 'design'],
    config: {
      head: createNode('head-game', 'gpt4o-mini', 'Creative Director', 'head', '#10a37f', 'Head', {
        temperature: 0.7,
        systemPrompt: 'Coordinate designers and writers to produce cohesive game concepts.',
      }),
      leg: createNode('leg-game', 'team', 'Design Team Loop', 'leg', '#a855f7', 'Execution', {
        mode: 'team',
      }),
      teamMembers: [
        {
          id: 'game-designer',
          name: 'Mechanics Designer',
          role: 'Builds gameplay loops',
          head: createNode('head-game-designer', 'gpt4o-mini', 'Designer Head', 'head', '#10a37f', 'Head', {
            temperature: 0.6,
            systemPrompt: 'Outline mechanics, progression, and balancing notes.',
          }),
          arms: [],
        },
        {
          id: 'game-writer',
          name: 'Lore Writer',
          role: 'Creates narrative flavor',
          head: createNode('head-game-writer', 'gpt4o-mini', 'Writer Head', 'head', '#10a37f', 'Head', {
            temperature: 0.75,
            systemPrompt: 'Craft lore, characters, and quest hooks.',
          }),
          arms: [],
        },
      ],
    },
  },
  {
    id: 'blueprint-agno-corrective-rag',
    name: 'Corrective RAG Analyst',
    description: 'Guardrailed RAG assistant based on the Corrective RAG tutorial, combining Tavily search and Qdrant.',
    category: 'Data & Analytics',
    icon: <FileSearch className="w-5 h-5" />,
    rating: 4.7,
    downloads: 623,
    featured: false,
    tags: ['rag', 'qdrant', 'tavily'],
    config: {
      head: createNode('head-corrective', 'gpt4o-mini', 'Corrective Brain', 'head', '#10a37f', 'Head', {
        temperature: 0.4,
        systemPrompt: 'Draft answers with retrieval evidence and correction steps.',
      }),
      arms: [
        createNode('arm-corrective-1', 'tavily-search', 'Evidence Search', 'arm', '#3b82f6', 'Tool', {
          searchDepth: 'advanced',
        }),
        createNode('arm-corrective-2', 'http-tool', 'Qdrant Retriever', 'arm', '#3b82f6', 'Tool', {
          baseUrl: 'http://localhost:6333',
        }),
      ],
      heart: createNode('heart-corrective', 'convo-memory', 'Correction Memory', 'heart', '#ec4899', 'Memory', {
        maxMessages: 7,
      }),
      leg: createNode('leg-corrective', 'single-agent', 'RAG Loop', 'leg', '#f97316', 'Execution', {
        mode: 'single',
      }),
    },
  },
  {
    id: 'blueprint-agno-local-news',
    name: 'Local News Agent',
    description: 'Local News Swarm agent blueprint tailored for Agno to watch geo-tagged stories.',
    category: 'Productivity',
    icon: <Sparkles className="w-5 h-5" />,
    rating: 4.5,
    downloads: 512,
    featured: false,
    tags: ['news', 'local', 'swarm'],
    config: {
      head: createNode('head-local-news', 'gpt4o-mini', 'Community Reporter', 'head', '#10a37f', 'Head', {
        temperature: 0.55,
        systemPrompt: 'Summarize neighborhood updates and propose follow-up questions.',
      }),
      arms: [
        createNode('arm-local-news-1', 'tavily-search', 'Geo Search', 'arm', '#3b82f6', 'Tool', {
          searchDepth: 'basic',
          include_answer: true,
        }),
      ],
      leg: createNode('leg-local-news', 'single-agent', 'Swarm Loop', 'leg', '#f97316', 'Execution', {
        mode: 'single',
      }),
    },
  },
  {
    id: 'blueprint-agno-voice-rag',
    name: 'Voice RAG Concierge',
    description: 'Voice RAG agent from awesome-llm-apps that routes speech queries through retrieval chains.',
    category: 'Customer Support',
    icon: <MessageSquare className="w-5 h-5" />,
    rating: 4.6,
    downloads: 547,
    featured: false,
    tags: ['voice', 'rag', 'support'],
    config: {
      head: createNode('head-voice-rag', 'gpt4o-mini', 'Voice RAG Core', 'head', '#10a37f', 'Head', {
        temperature: 0.5,
        systemPrompt: 'Use retrieval evidence to answer spoken questions and log action items.',
      }),
      arms: [
        createNode('arm-voice-rag-1', 'http-tool', 'Telephony Gateway', 'arm', '#3b82f6', 'Tool', {
          baseUrl: 'https://api.twilio.com',
        }),
        createNode('arm-voice-rag-2', 'http-tool', 'Vector DB', 'arm', '#3b82f6', 'Tool', {
          baseUrl: 'http://localhost:6333',
        }),
      ],
      heart: createNode('heart-voice-rag', 'convo-memory', 'Call Transcript Memory', 'heart', '#ec4899', 'Memory', {
        maxMessages: 10,
      }),
      leg: createNode('leg-voice-rag', 'single-agent', 'Voice Retrieval Loop', 'leg', '#f97316', 'Execution', {
        mode: 'single',
      }),
    },
  },
];

interface MarketplaceProps {
  onBack: () => void;
  onUseBlueprint: (config: AgentConfiguration) => void;
  isAuthenticated: boolean;
  onOpenMyAgents?: () => void;
  onOpenSettings?: () => void;
  onOpenAuthDialog?: () => void;
}

export function Marketplace({ 
  onBack, 
  onUseBlueprint, 
  isAuthenticated,
  onOpenMyAgents,
  onOpenSettings,
  onOpenAuthDialog 
}: MarketplaceProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('All');
  const [selectedBlueprint, setSelectedBlueprint] = useState<AgentBlueprint | null>(null);

  const categories = ['All', 'Customer Support', 'Data & Analytics', 'Content Creation', 'Productivity', 'Sales & Marketing'];

  const filteredBlueprints = SAMPLE_BLUEPRINTS.filter(blueprint => {
    const matchesSearch = blueprint.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      blueprint.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
      blueprint.tags.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()));
    const matchesCategory = selectedCategory === 'All' || blueprint.category === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  const featuredBlueprints = filteredBlueprints.filter(b => b.featured);
  const regularBlueprints = filteredBlueprints.filter(b => !b.featured);

  const handleUseBlueprint = (blueprint: AgentBlueprint) => {
    onUseBlueprint(JSON.parse(JSON.stringify(blueprint.config)));
    toast.success(`Loaded "${blueprint.name}" blueprint`);
    onBack();
  };


  // Blueprint card component - fixed size to prevent reflow
  const BlueprintCard = ({ blueprint, isFeatured }: { blueprint: AgentBlueprint; isFeatured: boolean }) => (
    <Card
      onClick={() => setSelectedBlueprint(blueprint)}
      className={`cursor-pointer transition-colors p-4 h-[200px] w-full flex flex-col ${selectedBlueprint?.id === blueprint.id
          ? 'bg-green-950/20 border-green-500'
          : 'bg-gray-900/50 border-gray-800 hover:border-gray-700'
        }`}
    >
      <div className="flex items-start gap-3 mb-3">
        <div className={`w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0 ${isFeatured
            ? 'bg-gradient-to-br from-green-600 to-lime-600 text-white shadow-lg shadow-green-500/20'
            : 'bg-gray-700 text-gray-300'
          }`}>
          {blueprint.icon}
        </div>
        <div className="flex-1 min-w-0">
          <h3 className="text-base font-medium text-gray-100">{blueprint.name}</h3>
          <span className={`text-sm ${isFeatured ? 'text-green-400' : 'text-gray-500'}`}>
            {blueprint.category}
          </span>
        </div>
      </div>
      <p className="text-sm text-gray-400 mb-3 line-clamp-2 flex-1">{blueprint.description}</p>
      <div className="flex items-center justify-between text-sm text-gray-500 mb-3">
        <div className="flex items-center gap-1">
          <Star className="w-3.5 h-3.5" style={{ fill: '#eab308', color: '#eab308' }} />
          <span>{blueprint.rating}</span>
        </div>
        <div className="flex items-center gap-1">
          <Download className="w-3.5 h-3.5" />
          <span>{blueprint.downloads.toLocaleString()}</span>
        </div>
      </div>
      <div className="flex gap-1.5 flex-wrap overflow-hidden h-6">
        {blueprint.tags.map(tag => (
          <Badge key={tag} variant="outline" className="text-xs px-2 py-0.5 border-gray-700 text-gray-500" style={{ borderRadius: '8px' }}>
            {tag}
          </Badge>
        ))}
      </div>
    </Card>
  );

  return (
    <div className="h-full w-full flex flex-col bg-gray-950">
      {/* Top Bar */}
      <TopBar
        subtitle="Monster Marketplace"
        isAuthenticated={isAuthenticated}
        onNavigateHome={onBack}
        onOpenMarketplace={() => {}}
        onOpenMyAgents={onOpenMyAgents}
        onOpenSettings={onOpenSettings}
        onOpenAuthDialog={onOpenAuthDialog}
      />

      {/* Marketplace Header */}
      <div className="border-b border-gray-800 bg-gray-950 flex-shrink-0 px-4 sm:px-6 py-4">
        <h2 className="text-lg font-medium text-gray-100 mb-1">Agent Marketplace</h2>
        <p className="text-xs text-gray-400">Browse and use pre-built agent blueprints</p>
      </div>

      {/* Search and Filters */}
      <div className="px-4 sm:px-6 py-4 border-b border-gray-800 space-y-3">
        <div className="relative">
          <Search className="absolute top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" style={{ left: '16px' }} />
          <Input
            type="text"
            placeholder="Search blueprints..."
            value={searchQuery}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) => setSearchQuery(e.target.value)}
            className="h-10 bg-gray-900 border-gray-800 text-gray-100 text-sm placeholder:text-gray-500 rounded-lg"
            style={{ paddingLeft: '44px' }}
          />
        </div>
        <div className="flex gap-2 overflow-x-auto pb-2">
          {categories.map(category => (
            <Button
              key={category}
              onClick={() => setSelectedCategory(category)}
              variant={selectedCategory === category ? 'default' : 'outline'}
              size="sm"
              className={`text-xs h-8 whitespace-nowrap ${selectedCategory === category
                  ? 'bg-gradient-to-r from-green-600 to-lime-600 text-white'
                  : 'bg-gray-900 border-gray-700 text-gray-300 hover:bg-gray-800'
                }`}
              style={{ borderRadius: '10px' }}
            >
              {category}
            </Button>
          ))}
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 min-h-0 overflow-hidden">
        <ScrollArea className="h-full">
          <div className="p-4 sm:p-6 space-y-8">
            {/* Featured Section */}
            {featuredBlueprints.length > 0 && (
              <div>
                <div className="flex items-center gap-2" style={{ paddingBottom: '20px' }}>
                  <Star className="w-5 h-5" style={{ fill: '#eab308', color: '#eab308' }} />
                  <h2 className="text-lg font-medium text-gray-100">Featured Blueprints</h2>
                </div>
                <div style={{ display: 'grid', gap: '16px', gridTemplateColumns: 'repeat(auto-fill, minmax(450px, 1fr))' }}>
                  {featuredBlueprints.map(blueprint => (
                    <BlueprintCard key={blueprint.id} blueprint={blueprint} isFeatured={true} />
                  ))}
                </div>
              </div>
            )}

            {/* All Blueprints */}
            {regularBlueprints.length > 0 && (
              <div>
                <h2 className="text-lg font-medium text-gray-100" style={{ paddingBottom: '20px', paddingTop: '20px' }}>All Blueprints</h2>
                <div style={{ display: 'grid', gap: '16px', gridTemplateColumns: 'repeat(auto-fill, minmax(450px, 1fr))' }}>
                  {regularBlueprints.map(blueprint => (
                    <BlueprintCard key={blueprint.id} blueprint={blueprint} isFeatured={false} />
                  ))}
                </div>
              </div>
            )}

            {filteredBlueprints.length === 0 && (
              <div className="text-center py-12">
                <Search className="w-8 h-8 text-gray-600 mx-auto mb-2" />
                <p className="text-gray-400 text-sm">No blueprints found</p>
              </div>
            )}
          </div>
        </ScrollArea>
      </div>

      {/* Blueprint Detail Dialog */}
      <Dialog open={!!selectedBlueprint} onOpenChange={(open) => !open && setSelectedBlueprint(null)}>
        <DialogContent className="bg-gray-950 border-gray-800 text-gray-100 max-w-lg max-h-[80vh] overflow-hidden flex flex-col">
          {selectedBlueprint && (
            <>
              <DialogHeader>
                <div className="flex items-start gap-3">
                  <div className="w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0 bg-gradient-to-br from-green-600 to-lime-600 text-white shadow-lg shadow-green-500/20">
                    {selectedBlueprint.icon}
                  </div>
                  <div className="flex-1 min-w-0">
                    <DialogTitle className="text-lg font-medium text-gray-100">{selectedBlueprint.name}</DialogTitle>
                    <span className="text-sm text-green-400">{selectedBlueprint.category}</span>
                  </div>
                </div>
              </DialogHeader>

              <div className="flex-1 overflow-y-auto space-y-4 pr-2">
                <div className="flex items-center gap-4 text-sm text-gray-400">
                  <div className="flex items-center gap-1">
                    <Star className="w-4 h-4" style={{ fill: '#eab308', color: '#eab308' }} />
                    <span>{selectedBlueprint.rating} rating</span>
                  </div>
                  <div className="flex items-center gap-1">
                    <Download className="w-4 h-4" />
                    <span>{selectedBlueprint.downloads} uses</span>
                  </div>
                </div>

                <p className="text-sm text-gray-400">{selectedBlueprint.description}</p>

                {/* Tags */}
                <div>
                  <h4 className="text-sm text-gray-400 mb-2">Tags</h4>
                  <div className="flex gap-2 flex-wrap">
                    {selectedBlueprint.tags.map(tag => (
                      <Badge key={tag} variant="outline" className="text-xs border-gray-700 text-gray-400" style={{ borderRadius: '8px' }}>
                        {tag}
                      </Badge>
                    ))}
                  </div>
                </div>

                {/* Configuration */}
                <div>
                  <h4 className="text-sm text-gray-400 mb-3">What's Included</h4>
                  <div className="space-y-2">
                    {selectedBlueprint.config.head && (
                      <div className="flex items-center gap-3 p-3 bg-gray-900 border border-gray-800 rounded-lg">
                        <div className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0" style={{ backgroundColor: 'rgba(147, 51, 234, 0.3)' }}>
                          <Brain className="w-5 h-5" style={{ color: '#c084fc' }} />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="text-sm font-medium text-gray-200">{selectedBlueprint.config.head.name}</div>
                          <div className="text-xs text-gray-500">Head (LLM)</div>
                        </div>
                      </div>
                    )}
                    {selectedBlueprint.config.arms.length > 0 && (
                      <div className="flex items-start gap-3 p-3 bg-gray-900 border border-gray-800 rounded-lg">
                        <div className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0" style={{ backgroundColor: 'rgba(37, 99, 235, 0.3)' }}>
                          <Wrench className="w-5 h-5" style={{ color: '#60a5fa' }} />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="text-sm font-medium text-gray-200">
                            {selectedBlueprint.config.arms.length} Tool{selectedBlueprint.config.arms.length !== 1 ? 's' : ''}
                          </div>
                          <div className="space-y-0.5">
                            {selectedBlueprint.config.arms.map((arm, index) => (
                              <div key={index} className="text-xs text-gray-500">• {arm.name}</div>
                            ))}
                          </div>
                        </div>
                      </div>
                    )}
                    {selectedBlueprint.config.heart && (
                      <div className="flex items-center gap-3 p-3 bg-gray-900 border border-gray-800 rounded-lg">
                        <div className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0" style={{ backgroundColor: 'rgba(236, 72, 153, 0.3)' }}>
                          <Heart className="w-5 h-5" style={{ color: '#f472b6' }} />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="text-sm font-medium text-gray-200">{selectedBlueprint.config.heart.name}</div>
                          <div className="text-xs text-gray-500">Memory/Knowledge</div>
                        </div>
                      </div>
                    )}
                    {selectedBlueprint.config.leg && (
                      <div className="flex items-center gap-3 p-3 bg-gray-900 border border-gray-800 rounded-lg">
                        <div className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0" style={{ backgroundColor: 'rgba(249, 115, 22, 0.3)' }}>
                          <Footprints className="w-5 h-5" style={{ color: '#fb923c' }} />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="text-sm font-medium text-gray-200">{selectedBlueprint.config.leg.name}</div>
                          <div className="text-xs text-gray-500">Execution Mode</div>
                        </div>
                      </div>
                    )}
                    {selectedBlueprint.config.spine && (
                      <div className="flex items-center gap-3 p-3 bg-gray-900 border border-gray-800 rounded-lg">
                        <div className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0" style={{ backgroundColor: 'rgba(6, 182, 212, 0.3)' }}>
                          <Shield className="w-5 h-5" style={{ color: '#22d3ee' }} />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="text-sm font-medium text-gray-200">{selectedBlueprint.config.spine.name}</div>
                          <div className="text-xs text-gray-500">Guardrails</div>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Action Button */}
              <div className="pt-4 border-t border-gray-800">
                <Button
                  onClick={() => handleUseBlueprint(selectedBlueprint)}
                  className="w-full h-12 rounded-lg text-white font-semibold shadow-lg shadow-green-900/30 border-0"
                  style={{ background: 'linear-gradient(to right, #00b140, #12a72f, #55a100)' }}
                >
                  <Download className="w-5 h-5 mr-2" />
                  Use This Blueprint
                </Button>
              </div>
            </>
          )}
        </DialogContent>
      </Dialog>

      {/* Footer */}
      <Footer />
    </div>
  );
}
