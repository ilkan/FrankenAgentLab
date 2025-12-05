import { Github, Zap, Heart } from 'lucide-react';

export function Footer() {
  return (
    <footer className="h-12 border-t border-gray-800 bg-gray-950 flex items-center justify-between px-6 flex-shrink-0 text-sm">
      <div className="flex items-center gap-2 text-gray-500">
        <Zap className="w-4 h-4 text-green-500" />
        <span>FrankenAgent Lab</span>
        <span className="text-gray-700">•</span>
        <span className="text-gray-600">v0.1.0</span>
      </div>

      <div className="flex items-center gap-6">
        <a
          href="https://ilkanyildirim.medium.com"
          target="_blank"
          rel="noopener noreferrer"
          className="text-gray-500 hover:text-gray-300 transition-colors"
        >
          Powered by Ilkan
        </a>
        
        <div className="flex items-center gap-1 text-gray-600">
          <span>Made with</span>
          <Heart className="w-3 h-3 text-red-400 fill-red-400" />
          <span>for AI builders</span>
        </div>

        <a
          href="https://github.com/ilkan"
          target="_blank"
          rel="noopener noreferrer"
          className="text-gray-500 hover:text-gray-300 transition-colors flex items-center gap-1"
        >
          <Github className="w-4 h-4" />
          <span>GitHub</span>
        </a>
      </div>
    </footer>
  );
}
