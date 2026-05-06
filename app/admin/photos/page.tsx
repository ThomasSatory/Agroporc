import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { getAllPhotos } from "@/lib/db";
import AdminPhotosClient from "./AdminPhotosClient";

export default async function AdminPhotosPage() {
  const cookieStore = await cookies();
  if (cookieStore.get("pdj-admin")?.value !== "1") {
    redirect("/admin/login");
  }

  const photos = await getAllPhotos();
  return <AdminPhotosClient initialPhotos={photos} />;
}
