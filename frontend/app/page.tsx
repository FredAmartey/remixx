import { Hero } from "@/components/Hero";
import { AlbumRow } from "@/components/AlbumRow";
import { Sidebar } from "@/components/Sidebar";
import { NowPlayingBar } from "@/components/NowPlayingBar";

export default function Home() {
  return (
    <div className="flex min-h-screen bg-walnut">
      <Sidebar />
      <main className="flex-1 ml-[240px] mb-24 px-16 py-12 overflow-x-hidden">
        <Hero />
        <AlbumRow />
      </main>
      <NowPlayingBar />
    </div>
  );
}
