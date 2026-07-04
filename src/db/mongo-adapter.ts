import { MongoClient } from "mongodb";

const client = new MongoClient(process.env.MONGO_URI!);
client.connect();

export async function insertPayment(amount: number, userId: string) {
  const db = client.db("paylink");
  return db.collection("payments").insertOne({ amount, userId, createdAt: new Date() });
}
