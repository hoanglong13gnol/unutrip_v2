import { optionalAuthMiddleware } from "../../auth.js";
import {
  listDestinations,
  listFeatured,
  listNearby,
  getDestinationDetail
} from "./destinations.controller.js";

export function registerDestinationRoutes(router) {
  router.get("/destinations", optionalAuthMiddleware, listDestinations);
  router.get("/destinations/featured", optionalAuthMiddleware, listFeatured);
  router.get("/destinations/nearby", optionalAuthMiddleware, listNearby);
  router.get("/destinations/:id", optionalAuthMiddleware, getDestinationDetail);
}
