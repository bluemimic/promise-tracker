from locust import HttpUser, between, task


class PromiseListUser(HttpUser):
    wait_time = between(0.5, 2)

    @task(5)
    def list_promises(self):
        self.client.get("/promises/promises/")

    @task(1)
    def list_promises_page(self):
        self.client.get("/promises/promises/?page=2")
