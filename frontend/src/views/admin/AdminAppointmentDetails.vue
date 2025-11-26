<template>
  <div class="container py-4">
    <h2 class="fw-bold mb-3">Appointment Details</h2>
    <p class="text-muted small">
      Appointment ID from route: <strong>{{ id }}</strong>
    </p>
    <p class="text-muted small">
      Later you can fetch <code>/admin/appointments/{{ id }}</code> and show
      patient history, doctor info, etc.
    </p>
  </div>
</template>

<script setup>
const props = defineProps({
  id: {
    type: String,
    required: true,
  },
})
</script>
