import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import staffApi from '../../services/staffApi';

export const reassignTicket = createAsyncThunk(
  'staff/reassignTicket',
  async ({ ticketId, updates }, { rejectWithValue }) => {
    try {
      const data = await staffApi.reassignTicket(ticketId, updates);
      return data;
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);