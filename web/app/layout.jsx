import "./globals.css";
import Navigation from "./navigation";
export const metadata = {
  title: "Northgate Bank | Fraud operations",
  description: "Alert preparation and workload analysis",
};
export default function Layout({ children }) {
  return (
    <html lang="en" data-theme="light">
      <body suppressHydrationWarning>
        <Navigation />
        <main id="main">{children}</main>
      </body>
    </html>
  );
}
