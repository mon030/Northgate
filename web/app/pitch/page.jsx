import Deck from "./slides";
export const metadata = { title: "Northgate pilot | Team presentation" };
export default function Pitch() {
  return (
    <>
      <header>
        <div>
          <p className="kicker">Executive committee</p>
          <h1>Alert preparation pilot</h1>
        </div>
      </header>
      <Deck />
    </>
  );
}
